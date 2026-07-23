"""Read-only consumer for the shared JIVO product-identity map.

The identity map is generated outside jivo-desk.  This module only opens it for
reading, validates the complete release contract, and expands exact identifiers
into their related price listings, canonical JIDs, and qualified Factory items.

Names are deliberately absent from :meth:`resolve`: they are candidates for
``search`` only and must never become an operational join key.
"""

import json
import hashlib
import math
import os
import posixpath
import re
import urllib.parse


MAP_FILENAME = "product-identity-map.json"
ATTESTATION_FILENAME = "release-attestation.json"
SUPPORTED_SCHEMA_MAJOR = 1
CONTRACT_NAME = "jivo-product-identity"
ATTESTATION_FORMAT_VERSION = "1.0.0"
ATTESTATION_CONTRACT_NAME = "jivo-product-identity-release-attestation"
TRUSTED_VERIFIER_VERSION = "1.1.0"
TRUSTED_VERIFIER_CHECK_COUNT = 74761
# Deliberately compiled into the consumer: neither the map nor its detached
# attestation can nominate a new trusted digest for itself.
TRUSTED_ATTESTATION_SHA256 = (
    "sha256:ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac"
)

REQUIRED_ARRAYS = (
    "sources",
    "factory_scopes",
    "products",
    "price_skus",
    "listings",
    "factory_items",
    "resolutions",
    "jid_aliases",
    "jid_conflicts",
    "factory_item_accounting",
    "factory_code_collisions",
)

_COVERAGE_DIMENSIONS = {
    "price_skus": "price_skus",
    "listings": "listings",
    "jids": "products",
    "factory_items": "factory_items",
}
_COVERAGE_ZERO_FIELDS = (
    "unresolved_listings",
    "ambiguous_listings",
    "open_jid_conflicts",
    "unknown_factory_collisions",
)
_EVIDENCE_KINDS = {
    "exact_price_code",
    "exact_listing_identity",
    "exact_source_sap",
    "qualified_factory_record",
    "review_decision",
    "complete_catalog_absence",
    "accounting_disposition",
}
_EXACT_SOURCE_EVIDENCE_KINDS = {
    "exact_price_code",
    "exact_listing_identity",
    "exact_source_sap",
}


class IdentityMapError(Exception):
    """The map cannot safely be used for an operational identity lookup."""


class IdentityNotFoundError(Exception):
    """An exact operational identifier was not found."""


class IdentityAmbiguousError(Exception):
    """An exact shorthand identifier points at more than one entity."""

    def __init__(self, identifier, candidates):
        self.identifier = identifier
        self.candidates = candidates
        super().__init__(
            "identifier %r is ambiguous; use a full key (%s)"
            % (identifier, ", ".join(candidates))
        )


def _strict_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key %r" % key)
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError("non-finite JSON number %s is not allowed" % value)


def _sha256_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _exact_keys(value, expected, label, errors):
    if not isinstance(value, dict):
        errors.append("%s must be an object" % label)
        return False
    actual = set(value)
    expected = set(expected)
    if actual != expected:
        errors.append(
            "%s keys differ (missing=%r, unexpected=%r)"
            % (label, sorted(expected - actual), sorted(actual - expected))
        )
        return False
    return True


def _attested_file(attestation_path, uri, label, errors):
    """Resolve one normalized bundle-relative URI without allowing escape."""
    if not isinstance(uri, str) or not uri:
        errors.append("%s.uri must be a non-empty string" % label)
        return None
    if "\\" in uri or uri.startswith("/") or posixpath.normpath(uri) != uri:
        errors.append("%s.uri must be a normalized relative POSIX path" % label)
        return None
    parts = uri.split("/")
    if any(part in ("", ".", "..") for part in parts):
        errors.append("%s.uri may not contain empty, '.' or '..' segments" % label)
        return None
    base = os.path.realpath(os.path.dirname(attestation_path))
    candidate = os.path.realpath(os.path.join(base, *parts))
    try:
        inside = os.path.commonpath((base, candidate)) == base
    except ValueError:
        inside = False
    if not inside:
        errors.append("%s.uri escapes the attested release directory" % label)
        return None
    if not os.path.isfile(candidate):
        errors.append("%s is missing: %s" % (label, candidate))
        return None
    return candidate


def _verify_release_attestation(
    map_path,
    map_raw,
    data,
    trusted_attestation_sha256,
    attestation_path=None,
):
    """Validate the detached release and every frozen evidence artifact."""
    errors = []
    path = os.path.abspath(
        attestation_path
        or os.path.join(os.path.dirname(map_path), ATTESTATION_FILENAME)
    )
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
        attestation = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except OSError as exc:
        raise IdentityMapError("release attestation cannot be read: %s" % exc)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise IdentityMapError("release attestation is not valid JSON: %s" % exc)

    attestation_sha256 = _sha256_bytes(raw)
    if attestation_sha256 != trusted_attestation_sha256:
        errors.append(
            "release attestation SHA-256 is not the compiled trusted release "
            "(%s)" % attestation_sha256
        )

    if not _exact_keys(
        attestation,
        (
            "format_version",
            "contract_name",
            "dataset_version",
            "schema_version",
            "release_status",
            "map",
            "evidence_artifacts",
            "verification",
        ),
        "release attestation",
        errors,
    ):
        raise IdentityMapError(
            "release attestation failed validation: %s" % "; ".join(errors)
        )

    contract = data.get("contract", {}) if isinstance(data, dict) else {}
    expected_scalars = {
        "format_version": ATTESTATION_FORMAT_VERSION,
        "contract_name": ATTESTATION_CONTRACT_NAME,
        "dataset_version": contract.get("dataset_version"),
        "schema_version": contract.get("schema_version"),
        "release_status": "released",
    }
    for field, expected in expected_scalars.items():
        if attestation.get(field) != expected:
            errors.append(
                "release attestation %s differs: expected %r, got %r"
                % (field, expected, attestation.get(field))
            )

    map_record = attestation.get("map")
    if _exact_keys(map_record, ("uri", "sha256"), "release attestation map", errors):
        attested_map_path = _attested_file(
            path, map_record.get("uri"), "release attestation map", errors
        )
        if attested_map_path is not None and os.path.realpath(attested_map_path) != os.path.realpath(map_path):
            errors.append("release attestation map.uri does not identify the requested map")
        if map_record.get("sha256") != _sha256_bytes(map_raw):
            errors.append("map SHA-256 does not match the trusted release attestation")

    source_rows = data.get("sources", []) if isinstance(data, dict) else []
    expected_sources = {
        row.get("source_id"): row
        for row in source_rows
        if isinstance(row, dict) and isinstance(row.get("source_id"), str)
    }
    attested_sources = {}
    evidence_rows = attestation.get("evidence_artifacts")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        errors.append("release attestation evidence_artifacts must be a non-empty array")
        evidence_rows = []
    for position, row in enumerate(evidence_rows):
        label = "release attestation evidence_artifacts[%d]" % position
        if not _exact_keys(row, ("source_id", "uri", "sha256"), label, errors):
            continue
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append("%s.source_id must be a non-empty string" % label)
            continue
        if source_id in attested_sources:
            errors.append("release attestation repeats source_id %r" % source_id)
            continue
        attested_sources[source_id] = row
        source = expected_sources.get(source_id)
        if source is None:
            errors.append("release attestation has unknown source_id %r" % source_id)
        elif row.get("sha256") != source.get("content_sha256"):
            errors.append("attested source hash differs from map source record: %s" % source_id)
        evidence_path = _attested_file(path, row.get("uri"), label, errors)
        if evidence_path is not None:
            with open(evidence_path, "rb") as handle:
                evidence_sha256 = _sha256_bytes(handle.read())
            if evidence_sha256 != row.get("sha256"):
                errors.append("evidence artifact hash drift: %s" % source_id)
    if set(attested_sources) != set(expected_sources):
        errors.append(
            "release attestation evidence source set differs from the map "
            "(missing=%r, unexpected=%r)"
            % (
                sorted(set(expected_sources) - set(attested_sources)),
                sorted(set(attested_sources) - set(expected_sources)),
            )
        )

    verification = attestation.get("verification")
    if _exact_keys(
        verification,
        ("verifier_version", "check_count"),
        "release attestation verification",
        errors,
    ):
        if verification.get("verifier_version") != TRUSTED_VERIFIER_VERSION:
            errors.append("release attestation verifier_version is unsupported")
        if verification.get("check_count") != TRUSTED_VERIFIER_CHECK_COUNT:
            errors.append("release attestation check_count is not the trusted release count")

    if errors:
        shown = errors[:20]
        suffix = "" if len(errors) <= len(shown) else "; ... %d more" % (
            len(errors) - len(shown)
        )
        raise IdentityMapError(
            "release attestation failed validation: %s%s"
            % ("; ".join(shown), suffix)
        )
    return {
        "path": path,
        "sha256": attestation_sha256,
        "data": attestation,
    }


def _ancestors(path):
    """Yield an absolute path and each parent exactly once."""
    current = os.path.abspath(path)
    seen = set()
    while current not in seen:
        seen.add(current)
        yield current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


def find_map_path(explicit=None, environ=None, cwd=None):
    """Resolve the shared map with explicit > environment > repository order.

    Repository discovery starts from both the current directory and this
    installed package.  At every ancestor it checks the two layouts used by the
    source checkout and installed CLI bundle::

        <repo>/CLI/product-identity/v1/product-identity-map.json
        <CLI>/product-identity/v1/product-identity-map.json
    """
    env = os.environ if environ is None else environ
    requested = explicit or env.get("JIVO_PRODUCT_IDENTITY_MAP")
    if requested:
        path = os.path.abspath(os.path.expanduser(str(requested)))
        if not os.path.isfile(path):
            raise IdentityMapError("identity map not found: %s" % path)
        return path

    starts = [cwd or os.getcwd(), os.path.dirname(__file__)]
    candidates = []
    seen = set()
    for start in starts:
        for parent in _ancestors(start):
            for relative in (
                os.path.join("CLI", "product-identity", "v1", MAP_FILENAME),
                os.path.join("product-identity", "v1", MAP_FILENAME),
            ):
                candidate = os.path.join(parent, relative)
                if candidate in seen:
                    continue
                seen.add(candidate)
                candidates.append(candidate)
                if os.path.isfile(candidate):
                    return candidate
    raise IdentityMapError(
        "identity map not found; pass --identity-map, set "
        "JIVO_PRODUCT_IDENTITY_MAP, or install %s (%d locations checked)"
        % (os.path.join("CLI", "product-identity", "v1", MAP_FILENAME), len(candidates))
    )


def _required_text(row, field, label, errors):
    value = row.get(field) if isinstance(row, dict) else None
    if not isinstance(value, str) or not value.strip():
        errors.append("%s.%s must be a non-empty string" % (label, field))
        return None
    return value


def _index_unique(rows, field, label, errors):
    result = {}
    for position, row in enumerate(rows):
        item_label = "%s[%d]" % (label, position)
        if not isinstance(row, dict):
            errors.append("%s must be an object" % item_label)
            continue
        key = _required_text(row, field, item_label, errors)
        if key is None:
            continue
        if key in result:
            errors.append("duplicate %s %r" % (field, key))
            continue
        result[key] = row
    return result


def _product_key(row):
    """Return the v1 product key, falling back to the original JID-only shape."""
    if not isinstance(row, dict):
        return None
    key = row.get("product_key")
    if isinstance(key, str) and key.strip():
        return key
    jid = row.get("jid")
    return jid if isinstance(jid, str) and jid.strip() else None


def _index_products(rows, errors):
    """Index products whose JID may legitimately be null.

    Early v1 drafts used ``jid`` as the product primary key.  Released maps use
    ``product_key`` and retain an optional JID, so both shapes are accepted
    without inventing a JID for marketplace-only products.
    """
    by_key = {}
    by_jid = {}
    for position, row in enumerate(rows):
        label = "products[%d]" % position
        if not isinstance(row, dict):
            errors.append("%s must be an object" % label)
            continue
        key = _product_key(row)
        if key is None:
            errors.append("%s.product_key must be a non-empty string" % label)
            continue
        if key in by_key:
            errors.append("duplicate product_key %r" % key)
        else:
            by_key[key] = row
        jid = row.get("jid")
        if jid is not None and (not isinstance(jid, str) or not jid.strip()):
            errors.append("%s.jid must be a non-empty string or null" % label)
        elif isinstance(jid, str):
            if jid in by_jid:
                errors.append("duplicate jid %r" % jid)
            else:
                by_jid[jid] = row
    return by_key, by_jid


def _validate_evidence(
    value,
    label,
    sources,
    errors,
    minimum=1,
    required_kinds=None,
    require_one_of=None,
):
    """Validate evidence objects and their references to the source manifest."""
    if not isinstance(value, list) or len(value) < minimum:
        errors.append("%s.evidence must contain at least %d object(s)" % (label, minimum))
        return set()
    kinds = set()
    seen_claims = set()
    for position, evidence in enumerate(value):
        item_label = "%s.evidence[%d]" % (label, position)
        if not isinstance(evidence, dict):
            errors.append("%s must be an object" % item_label)
            continue
        source_id = _required_text(evidence, "source_id", item_label, errors)
        pointer = _required_text(evidence, "pointer", item_label, errors)
        claim = _required_text(evidence, "claim", item_label, errors)
        kind = _required_text(evidence, "evidence_kind", item_label, errors)
        if source_id is not None and source_id not in sources:
            errors.append("%s references missing source %r" % (item_label, source_id))
        if kind is not None:
            if kind not in _EVIDENCE_KINDS:
                errors.append("%s has unsupported evidence_kind %r" % (item_label, kind))
            kinds.add(kind)
        if all(value is not None for value in (source_id, pointer, claim, kind)):
            identity = (source_id, pointer, claim, kind)
            if identity in seen_claims:
                errors.append("%s duplicates an earlier evidence claim" % item_label)
            seen_claims.add(identity)
    for required in required_kinds or ():
        if required not in kinds:
            errors.append("%s.evidence requires evidence_kind %r" % (label, required))
    if require_one_of and not (kinds & set(require_one_of)):
        errors.append(
            "%s.evidence requires one of: %s"
            % (label, ", ".join(sorted(require_one_of)))
        )
    return kinds


def _schema_major(version):
    if not isinstance(version, str):
        return None
    match = re.match(r"^(\d+)(?:\.|$)", version.strip())
    return int(match.group(1)) if match else None


def _is_nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def listing_key_for(platform, listing_id):
    """Canonical key for an observed platform-qualified listing ID."""
    if not isinstance(platform, str) or not platform.strip():
        return None
    if listing_id is None or isinstance(listing_id, bool):
        return None
    listing_id = str(listing_id).strip()
    if not listing_id:
        return None
    return "urn:jivo:listing:%s:%s" % (
        urllib.parse.quote(platform.strip().lower(), safe=""),
        urllib.parse.quote(listing_id, safe=""),
    )


class ProductIdentityMap:
    """A fully validated, indexed product-identity release."""

    def __init__(
        self,
        data,
        path,
        map_sha256=None,
        attestation_path=None,
        attestation_sha256=None,
    ):
        self.data = data
        self.path = path
        self.map_sha256 = map_sha256
        self.attestation_path = attestation_path
        self.attestation_sha256 = attestation_sha256
        indexes = self._validate(data)
        self.products = indexes["products"]
        self.products_by_jid = indexes["products_by_jid"]
        self.price_skus = indexes["price_skus"]
        self.listings = indexes["listings"]
        self.factory_items = indexes["factory_items"]
        self.factory_scopes = indexes["factory_scopes"]
        self.resolutions = indexes["resolutions"]
        self.jid_aliases = {
            row["alias_jid"]: row for row in data["jid_aliases"]
        }
        self.listings_by_platform_id = {
            (row["platform"].lower(), row["listing_id"]): row
            for row in data["listings"]
        }

        self.price_skus_by_code = {}
        for row in data["price_skus"]:
            code = row["source_product_code"]
            self.price_skus_by_code.setdefault(code, []).append(row)

        self.resolutions_by_listing = {}
        self.resolution_product_keys = indexes["resolution_product_keys"]
        self.resolutions_by_product = {}
        self.resolutions_by_factory = {}
        for row in data["resolutions"]:
            self.resolutions_by_listing[row["listing_key"]] = row
            product_key = self.resolution_product_keys[row["resolution_id"]]
            self.resolutions_by_product.setdefault(product_key, []).append(row)
            for binding in row.get("factory_bindings", []):
                key = binding["factory_item_key"]
                self.resolutions_by_factory.setdefault(key, []).append(row)

    @classmethod
    def load(
        cls,
        explicit_path=None,
        environ=None,
        cwd=None,
        _trusted_attestation_sha256=None,
        _attestation_path=None,
    ):
        """Load only a release chained to the compiled detached attestation.

        The two underscored arguments exist solely for direct fixture tests. No
        CLI flag or environment variable exposes them, so production commands
        always use the compiled trust anchor and co-located attestation.
        """
        path = find_map_path(explicit_path, environ=environ, cwd=cwd)
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
            data = json.loads(
                    raw.decode("utf-8"),
                    object_pairs_hook=_strict_json_object,
                    parse_constant=_reject_json_constant,
                )
        except OSError as exc:
            raise IdentityMapError("cannot read identity map %s: %s" % (path, exc))
        except (UnicodeError, ValueError, TypeError) as exc:
            raise IdentityMapError("identity map is not valid JSON: %s" % exc)
        map_sha256 = _sha256_bytes(raw)
        attestation = _verify_release_attestation(
            path,
            raw,
            data,
            _trusted_attestation_sha256 or TRUSTED_ATTESTATION_SHA256,
            attestation_path=_attestation_path,
        )
        return cls(
            data,
            path,
            map_sha256=map_sha256,
            attestation_path=attestation["path"],
            attestation_sha256=attestation["sha256"],
        )

    @staticmethod
    def _validate(data):
        errors = []
        if not isinstance(data, dict):
            raise IdentityMapError("identity map root must be an object")

        contract = data.get("contract")
        if not isinstance(contract, dict):
            errors.append("contract must be an object")
            contract = {}
        if contract.get("name") != CONTRACT_NAME:
            errors.append("contract.name must be %r" % CONTRACT_NAME)
        version = contract.get("schema_version")
        major = _schema_major(version)
        if major != SUPPORTED_SCHEMA_MAJOR:
            errors.append(
                "unsupported contract.schema_version %r (supported major: %d)"
                % (version, SUPPORTED_SCHEMA_MAJOR)
            )
        if str(contract.get("release_status", "")).lower() != "released":
            errors.append("contract.release_status must be 'released'")
        if contract.get("read_only") is not True:
            errors.append("contract.read_only must be true")
        for field in (
            "dataset_version",
            "generated_at",
            "generator_version",
        ):
            _required_text(contract, field, "contract", errors)

        for name in REQUIRED_ARRAYS:
            if not isinstance(data.get(name), list):
                errors.append("%s must be an array" % name)
                data[name] = []

        sources = _index_unique(data["sources"], "source_id", "sources", errors)
        products, products_by_jid = _index_products(data["products"], errors)
        price_skus = _index_unique(
            data["price_skus"], "price_sku_key", "price_skus", errors
        )
        listings = _index_unique(
            data["listings"], "listing_key", "listings", errors
        )
        factory_items = _index_unique(
            data["factory_items"], "factory_item_key", "factory_items", errors
        )
        factory_scopes = _index_unique(
            data["factory_scopes"],
            "factory_scope_key",
            "factory_scopes",
            errors,
        )
        resolutions = _index_unique(
            data["resolutions"], "resolution_id", "resolutions", errors
        )

        # Required identifying fields beyond the primary keys.
        for key, row in factory_scopes.items():
            label = "factory_scope %r" % key
            _required_text(row, "company_code", label, errors)
            _required_text(row, "sap_schema", label, errors)
        for key, row in products.items():
            _required_text(row, "canonical_name", "product %r" % key, errors)
            _required_text(row, "state", "product %r" % key, errors)
        for key, row in price_skus.items():
            label = "price_sku %r" % key
            _required_text(row, "source_namespace", label, errors)
            _required_text(row, "source_product_code", label, errors)
            _required_text(row, "display_name", label, errors)
            _required_text(row, "state", label, errors)
            if not isinstance(row.get("member_listing_keys"), list):
                errors.append("%s.member_listing_keys must be an array" % label)
            _validate_evidence(row.get("evidence"), label, sources, errors)
        for key, row in listings.items():
            label = "listing %r" % key
            for field in (
                "price_sku_key",
                "platform",
                "listing_id",
                "listing_id_kind",
                "title",
                "state",
            ):
                _required_text(row, field, label, errors)
            _validate_evidence(row.get("evidence"), label, sources, errors)
        for key, row in factory_items.items():
            label = "factory_item %r" % key
            for field in (
                "factory_scope_key",
                "company_code",
                "sap_schema",
                "item_code",
                "item_name",
                "item_class",
                "state",
            ):
                _required_text(row, field, label, errors)
            _validate_evidence(row.get("evidence"), label, sources, errors)

        accounting_by_factory = {}
        for position, row in enumerate(data["factory_item_accounting"]):
            label = "factory_item_accounting[%d]" % position
            if not isinstance(row, dict):
                errors.append("%s must be an object" % label)
                continue
            item_key = _required_text(row, "factory_item_key", label, errors)
            if item_key is not None:
                if item_key not in factory_items:
                    errors.append(
                        "%s references missing factory_item %r" % (label, item_key)
                    )
                if item_key in accounting_by_factory:
                    errors.append(
                        "%s duplicates accounting for factory_item %r"
                        % (label, item_key)
                    )
                else:
                    accounting_by_factory[item_key] = row
            disposition = row.get("disposition")
            if disposition not in (
                "mapped",
                "not_in_price_scraping_scope",
                "inactive",
                "non_retail",
            ):
                errors.append("%s.disposition is invalid" % label)
            if disposition != "mapped":
                _required_text(row, "reason", label, errors)
            elif row.get("reason") is not None and not isinstance(row.get("reason"), str):
                errors.append("%s.reason must be a string when present" % label)
            listing_keys = row.get("listing_keys")
            if not isinstance(listing_keys, list):
                errors.append("%s.listing_keys must be an array" % label)
            else:
                seen_listing_keys = set()
                for listing_key in listing_keys:
                    if not isinstance(listing_key, str) or not listing_key:
                        errors.append("%s has an invalid listing_key" % label)
                        continue
                    if listing_key in seen_listing_keys:
                        errors.append(
                            "%s repeats listing_key %r" % (label, listing_key)
                        )
                    seen_listing_keys.add(listing_key)
                    if listing_key not in listings:
                        errors.append(
                            "%s references missing listing %r" % (label, listing_key)
                        )
            _validate_evidence(
                row.get("evidence"),
                label,
                sources,
                errors,
                required_kinds={"accounting_disposition"},
            )
        missing_accounting = sorted(set(factory_items) - set(accounting_by_factory))
        if missing_accounting:
            errors.append(
                "factory_item_accounting is missing %d factory item(s): %s"
                % (len(missing_accounting), ", ".join(missing_accounting[:5]))
            )

        alias_jids = set()
        for position, row in enumerate(data["jid_aliases"]):
            label = "jid_aliases[%d]" % position
            if not isinstance(row, dict):
                errors.append("%s must be an object" % label)
                continue
            alias = _required_text(row, "alias_jid", label, errors)
            canonical = _required_text(row, "canonical_jid", label, errors)
            for field in ("relation", "decision_id", "reason"):
                _required_text(row, field, label, errors)
            if alias is not None and alias not in products_by_jid:
                errors.append("%s references missing alias JID %r" % (label, alias))
            if alias is not None:
                if alias in alias_jids:
                    errors.append("duplicate alias_jid %r" % alias)
                alias_jids.add(alias)
            if canonical is not None and canonical not in products_by_jid:
                errors.append(
                    "%s references missing canonical JID %r" % (label, canonical)
                )
            if alias is not None and alias == canonical:
                errors.append("%s cannot alias a JID to itself" % label)
            _validate_evidence(row.get("evidence"), label, sources, errors)

        conflict_ids = set()
        blocking_conflicts = 0
        for position, row in enumerate(data["jid_conflicts"]):
            label = "jid_conflicts[%d]" % position
            if not isinstance(row, dict):
                errors.append("%s must be an object" % label)
                continue
            conflict_id = _required_text(row, "conflict_id", label, errors)
            for field in ("kind", "resolution_kind", "reason"):
                _required_text(row, field, label, errors)
            if conflict_id is not None:
                if conflict_id in conflict_ids:
                    errors.append("duplicate conflict_id %r" % conflict_id)
                conflict_ids.add(conflict_id)
            status = row.get("status")
            if status not in (
                "resolved",
                "resolved_for_price_scope",
                "open_out_of_price_scope",
            ):
                errors.append("%s.status is invalid" % label)
            blocking = row.get("blocking")
            if not isinstance(blocking, bool):
                errors.append("%s.blocking must be boolean" % label)
            elif blocking:
                blocking_conflicts += 1
            involved_jids = row.get("involved_jids")
            if not isinstance(involved_jids, list) or not involved_jids:
                errors.append("%s.involved_jids must be a non-empty array" % label)
            else:
                for jid in involved_jids:
                    if not isinstance(jid, str) or jid not in products_by_jid:
                        errors.append("%s references missing JID %r" % (label, jid))
            involved_listings = row.get("involved_listing_keys")
            if not isinstance(involved_listings, list):
                errors.append("%s.involved_listing_keys must be an array" % label)
            else:
                for listing_key in involved_listings:
                    if not isinstance(listing_key, str) or listing_key not in listings:
                        errors.append(
                            "%s references missing listing %r" % (label, listing_key)
                        )
            _validate_evidence(row.get("evidence"), label, sources, errors)

        collision_by_code = {}
        for position, row in enumerate(data["factory_code_collisions"]):
            label = "factory_code_collisions[%d]" % position
            if not isinstance(row, dict):
                errors.append("%s must be an object" % label)
                continue
            item_code = _required_text(row, "item_code", label, errors)
            if item_code is not None:
                if item_code in collision_by_code:
                    errors.append("duplicate collision item_code %r" % item_code)
                collision_by_code[item_code] = row
            if row.get("physical_relation") not in (
                "same_offer",
                "different_offer",
                "mixed",
            ):
                errors.append("%s.physical_relation is invalid" % label)
            item_keys = row.get("factory_item_keys")
            if not isinstance(item_keys, list) or len(item_keys) < 2:
                errors.append(
                    "%s.factory_item_keys must contain at least two keys" % label
                )
            else:
                all_string_keys = all(isinstance(value, str) for value in item_keys)
                if all_string_keys and len(item_keys) != len(set(item_keys)):
                    errors.append("%s.factory_item_keys contains duplicates" % label)
                for item_key in item_keys:
                    item = factory_items.get(item_key) if isinstance(item_key, str) else None
                    if item is None:
                        errors.append(
                            "%s references missing factory_item %r" % (label, item_key)
                        )
                    elif item.get("item_code") != item_code:
                        errors.append(
                            "%s includes factory_item %r with item_code %r"
                            % (label, item_key, item.get("item_code"))
                        )
            _validate_evidence(row.get("evidence"), label, sources, errors)

        expected_collision_keys = {}
        for item_key, item in factory_items.items():
            expected_collision_keys.setdefault(item.get("item_code"), []).append(item_key)
        expected_collision_keys = {
            code: sorted(keys)
            for code, keys in expected_collision_keys.items()
            if isinstance(code, str) and len(keys) > 1
        }
        if set(collision_by_code) != set(expected_collision_keys):
            missing = sorted(set(expected_collision_keys) - set(collision_by_code))
            unexpected = sorted(set(collision_by_code) - set(expected_collision_keys))
            if missing:
                errors.append(
                    "factory_code_collisions missing %d reused item_code(s): %s"
                    % (len(missing), ", ".join(missing[:5]))
                )
            if unexpected:
                errors.append(
                    "factory_code_collisions has %d non-collision code(s): %s"
                    % (len(unexpected), ", ".join(unexpected[:5]))
                )
        for code, expected_keys in expected_collision_keys.items():
            collision = collision_by_code.get(code)
            if collision is None:
                continue
            actual_keys = collision.get("factory_item_keys")
            if (
                isinstance(actual_keys, list)
                and all(isinstance(value, str) for value in actual_keys)
                and sorted(actual_keys) != expected_keys
            ):
                errors.append(
                    "factory_code_collisions %r does not list every qualified Factory key"
                    % code
                )

        # Stable tuples must be unique even when a producer accidentally emits
        # two different synthetic keys for the same operational entity.
        seen_price_tuples = {}
        for key, row in price_skus.items():
            value = (row.get("source_namespace"), row.get("source_product_code"))
            if not all(isinstance(part, str) and part for part in value):
                continue
            if value in seen_price_tuples:
                errors.append(
                    "price_skus %r and %r duplicate source identity %r"
                    % (seen_price_tuples[value], key, value)
                )
            else:
                seen_price_tuples[value] = key
        seen_listing_tuples = {}
        for key, row in listings.items():
            value = (row.get("platform"), row.get("listing_id"))
            if not all(isinstance(part, str) and part for part in value):
                continue
            if value in seen_listing_tuples:
                errors.append(
                    "listings %r and %r duplicate platform identity %r"
                    % (seen_listing_tuples[value], key, value)
                )
            else:
                seen_listing_tuples[value] = key
        seen_factory_tuples = {}
        for key, row in factory_items.items():
            value = (
                row.get("company_code"),
                row.get("sap_schema"),
                row.get("item_code"),
            )
            if not all(isinstance(part, str) and part for part in value):
                continue
            if value in seen_factory_tuples:
                errors.append(
                    "factory_items %r and %r duplicate qualified identity %r"
                    % (seen_factory_tuples[value], key, value)
                )
            else:
                seen_factory_tuples[value] = key

        # Bidirectional price-SKU/listing membership must agree exactly. One
        # platform listing may legitimately be observed by multiple human price
        # groups; price_sku_key is its primary group while price_sku_keys is the
        # complete membership set.
        listing_memberships = {}
        for sku_key, sku in price_skus.items():
            members = sku.get("member_listing_keys")
            if not isinstance(members, list):
                continue
            seen_members = set()
            for member in members:
                if not isinstance(member, str) or not member:
                    errors.append(
                        "price_sku %r has an invalid member_listing_key" % sku_key
                    )
                    continue
                if member in seen_members:
                    errors.append(
                        "price_sku %r repeats member listing %r" % (sku_key, member)
                    )
                    continue
                seen_members.add(member)
                listing_memberships.setdefault(member, []).append(sku_key)
                listing = listings.get(member)
                if listing is None:
                    errors.append(
                        "price_sku %r references missing listing %r"
                        % (sku_key, member)
                    )
        for listing_key, listing in listings.items():
            primary_sku_key = listing.get("price_sku_key")
            if (
                not isinstance(primary_sku_key, str)
                or primary_sku_key not in price_skus
            ):
                errors.append(
                    "listing %r references missing price_sku %r"
                    % (listing_key, primary_sku_key)
                )
            declared = listing.get("price_sku_keys")
            if declared is None:
                declared = [primary_sku_key]
            if (
                not isinstance(declared, list)
                or not declared
                or not all(isinstance(value, str) and value for value in declared)
            ):
                errors.append(
                    "listing %r.price_sku_keys must be a non-empty string array"
                    % listing_key
                )
                declared = []
            elif len(declared) != len(set(declared)):
                errors.append(
                    "listing %r.price_sku_keys contains duplicates" % listing_key
                )
            if primary_sku_key not in declared:
                errors.append(
                    "listing %r primary price_sku_key is absent from price_sku_keys"
                    % listing_key
                )
            for sku_key in declared:
                if sku_key not in price_skus:
                    errors.append(
                        "listing %r.price_sku_keys references missing price_sku %r"
                        % (listing_key, sku_key)
                    )
            observed = listing_memberships.get(listing_key, [])
            if sorted(observed) != sorted(declared):
                errors.append(
                    "listing %r price_sku_keys disagree with price_sku member lists"
                    % listing_key
                )
            source_memberships = listing.get("source_memberships")
            if source_memberships is not None:
                if not isinstance(source_memberships, list):
                    errors.append(
                        "listing %r.source_memberships must be an array" % listing_key
                    )
                else:
                    source_keys = []
                    for position, membership in enumerate(source_memberships):
                        label = "listing %r.source_memberships[%d]" % (
                            listing_key,
                            position,
                        )
                        if not isinstance(membership, dict):
                            errors.append("%s must be an object" % label)
                            continue
                        source_key = _required_text(
                            membership, "price_sku_key", label, errors
                        )
                        _required_text(membership, "role", label, errors)
                        if source_key is not None:
                            source_keys.append(source_key)
                    if sorted(source_keys) != sorted(declared):
                        errors.append(
                            "listing %r.source_memberships disagree with price_sku_keys"
                            % listing_key
                        )

        # Qualified Factory identity includes scope; a bare SAP code is never a key.
        for item_key, item in factory_items.items():
            scope_key = item.get("factory_scope_key")
            if not isinstance(scope_key, str) or scope_key not in factory_scopes:
                errors.append(
                    "factory_item %r references missing factory_scope %r"
                    % (item_key, scope_key)
                )
            else:
                scope = factory_scopes[scope_key]
                if item.get("company_code") != scope.get("company_code"):
                    errors.append(
                        "factory_item %r company_code disagrees with scope %r"
                        % (item_key, scope_key)
                    )
                if item.get("sap_schema") != scope.get("sap_schema"):
                    errors.append(
                        "factory_item %r sap_schema disagrees with scope %r"
                        % (item_key, scope_key)
                    )

        # Every resolution must be unique per listing and point to real entities.
        resolution_by_listing = {}
        resolution_product_keys = {}
        bound_listings_by_factory = {}
        for resolution_id, resolution in resolutions.items():
            label = "resolution %r" % resolution_id
            listing_key = _required_text(resolution, "listing_key", label, errors)
            state = _required_text(resolution, "state", label, errors)
            if state is not None and state not in ("verified", "retired"):
                errors.append("%s.state must be 'verified' or 'retired'" % label)
            for field in ("verification_method", "verified_by", "verified_at"):
                _required_text(resolution, field, label, errors)
            if listing_key is not None:
                if listing_key not in listings:
                    errors.append(
                        "%s references missing listing %r" % (label, listing_key)
                    )
                if listing_key in resolution_by_listing:
                    errors.append(
                        "listing %r has multiple resolutions (%r, %r)"
                        % (
                            listing_key,
                            resolution_by_listing[listing_key],
                            resolution_id,
                        )
                    )
                else:
                    resolution_by_listing[listing_key] = resolution_id
            product_key = resolution.get("canonical_product_key")
            canonical_jid = resolution.get("canonical_jid")
            if product_key is not None and (
                not isinstance(product_key, str) or not product_key.strip()
            ):
                errors.append(
                    "%s.canonical_product_key must be a non-empty string or null"
                    % label
                )
                product_key = None
            if canonical_jid is not None and (
                not isinstance(canonical_jid, str) or not canonical_jid.strip()
            ):
                errors.append(
                    "%s.canonical_jid must be a non-empty string or null" % label
                )
                canonical_jid = None
            if product_key is None and canonical_jid is not None:
                legacy_product = products_by_jid.get(canonical_jid)
                product_key = _product_key(legacy_product)
            product = products.get(product_key) if product_key is not None else None
            if product is None:
                errors.append(
                    "%s references missing product %r"
                    % (label, product_key or canonical_jid)
                )
            else:
                resolution_product_keys[resolution_id] = product_key
                product_jid = product.get("jid")
                if canonical_jid is not None and canonical_jid != product_jid:
                    errors.append(
                        "%s canonical_jid %r disagrees with product %r jid %r"
                        % (label, canonical_jid, product_key, product_jid)
                    )
            bindings = resolution.get("factory_bindings")
            if not isinstance(bindings, list):
                errors.append("%s.factory_bindings must be an array" % label)
                bindings = []
            seen_bindings = set()
            primary_by_scope = {}
            for position, binding in enumerate(bindings):
                binding_label = "%s.factory_bindings[%d]" % (label, position)
                if not isinstance(binding, dict):
                    errors.append("%s must be an object" % binding_label)
                    continue
                item_key = _required_text(
                    binding, "factory_item_key", binding_label, errors
                )
                _required_text(binding, "role", binding_label, errors)
                if not isinstance(binding.get("primary_for_scope"), bool):
                    errors.append(
                        "%s.primary_for_scope must be boolean" % binding_label
                    )
                elif binding.get("primary_for_scope") and item_key in factory_items:
                    scope_key = factory_items[item_key]["factory_scope_key"]
                    if scope_key in primary_by_scope:
                        errors.append(
                            "%s and %s are both primary_for_scope in %r"
                            % (primary_by_scope[scope_key], binding_label, scope_key)
                        )
                    else:
                        primary_by_scope[scope_key] = binding_label
                evidence = binding.get("evidence")
                _validate_evidence(
                    evidence,
                    binding_label,
                    sources,
                    errors,
                    minimum=2,
                    required_kinds={"qualified_factory_record"},
                    require_one_of=_EXACT_SOURCE_EVIDENCE_KINDS,
                )
                if item_key is not None:
                    if item_key not in factory_items:
                        errors.append(
                            "%s references missing factory_item %r"
                            % (binding_label, item_key)
                        )
                    if item_key in seen_bindings:
                        errors.append(
                            "%s repeats factory_item %r" % (label, item_key)
                        )
                    seen_bindings.add(item_key)
                    if item_key in factory_items and listing_key in listings:
                        bound_listings_by_factory.setdefault(item_key, set()).add(
                            listing_key
                        )
                ratio = binding.get("factory_uom_per_listing_offer")
                conversion_state = binding.get("conversion_state")
                if ratio is None:
                    if conversion_state != "not_proven":
                        errors.append(
                            "%s null Factory conversion requires conversion_state='not_proven'"
                            % binding_label
                        )
                elif not isinstance(ratio, dict):
                    errors.append(
                        "%s.factory_uom_per_listing_offer must be an object or null"
                        % binding_label
                    )
                else:
                    numerator = ratio.get("numerator")
                    denominator = ratio.get("denominator")
                    if (
                        not isinstance(numerator, (int, float))
                        or isinstance(numerator, bool)
                        or not math.isfinite(numerator)
                        or numerator <= 0
                    ):
                        errors.append("%s numerator must be positive" % binding_label)
                    if (
                        not isinstance(denominator, (int, float))
                        or isinstance(denominator, bool)
                        or not math.isfinite(denominator)
                        or denominator <= 0
                    ):
                        errors.append("%s denominator must be positive" % binding_label)

            mapping_state = resolution.get("factory_mapping_state")
            absence = resolution.get("factory_absence")
            if mapping_state == "verified":
                if not bindings:
                    errors.append("%s verified Factory mapping has no binding" % label)
                if absence is not None:
                    errors.append(
                        "%s verified Factory mapping must not have factory_absence"
                        % label
                    )
            elif mapping_state == "reviewed_absent":
                if bindings:
                    errors.append(
                        "%s reviewed_absent mapping must have no bindings" % label
                    )
                if not isinstance(absence, dict):
                    errors.append(
                        "%s reviewed_absent mapping requires factory_absence" % label
                    )
                else:
                    allowed_reasons = {
                        "not_present_in_complete_factory_catalog",
                        "not_factory_product",
                        "source_gap",
                    }
                    if absence.get("reason_code") not in allowed_reasons:
                        errors.append(
                            "%s.factory_absence.reason_code is invalid" % label
                        )
                    _required_text(absence, "reason", label + ".factory_absence", errors)
                    checked = absence.get("scopes_checked")
                    expected_scopes = set(factory_scopes)
                    if (
                        not isinstance(checked, list)
                        or not all(isinstance(value, str) for value in checked)
                        or len(checked) != len(set(checked))
                        or set(checked) != expected_scopes
                        or len(expected_scopes) != 3
                    ):
                        errors.append(
                            "%s.factory_absence.scopes_checked must contain all 3 Factory scopes"
                            % label
                        )
                    _validate_evidence(
                        absence.get("evidence"),
                        label + ".factory_absence",
                        sources,
                        errors,
                        minimum=2,
                        required_kinds={"complete_catalog_absence"},
                        require_one_of=_EXACT_SOURCE_EVIDENCE_KINDS,
                    )
            else:
                errors.append(
                    "%s.factory_mapping_state must be 'verified' or 'reviewed_absent'"
                    % label
                )

        # Factory accounting is not a decorative report: it must exactly mirror
        # the listing-level bindings served by this consumer.
        for item_key, accounting in accounting_by_factory.items():
            if item_key not in factory_items:
                continue
            declared = accounting.get("listing_keys")
            declared_set = (
                set(declared)
                if isinstance(declared, list)
                and all(isinstance(value, str) for value in declared)
                else set()
            )
            actual_set = bound_listings_by_factory.get(item_key, set())
            if accounting.get("disposition") == "mapped":
                if not declared_set:
                    errors.append(
                        "factory_item_accounting %r is mapped but lists no listings"
                        % item_key
                    )
                if declared_set != actual_set:
                    errors.append(
                        "factory_item_accounting %r listing_keys disagree with resolution bindings"
                        % item_key
                    )
            elif declared_set or actual_set:
                errors.append(
                    "factory_item_accounting %r is %r but has listing bindings"
                    % (item_key, accounting.get("disposition"))
                )

        # Every listing, including a retained retired listing, must resolve to a
        # real canonical product. Factory binding policy is checked above.
        for listing_key, listing in listings.items():
            resolution_id = resolution_by_listing.get(listing_key)
            if resolution_id is None:
                errors.append("listing %r has no resolution" % listing_key)

        coverage = data.get("coverage")
        if not isinstance(coverage, dict):
            errors.append("coverage must be an object")
            coverage = {}
        for dimension in _COVERAGE_DIMENSIONS:
            row = coverage.get(dimension)
            if not isinstance(row, dict):
                errors.append("coverage.%s must be an object" % dimension)
                continue
            for field in ("expected", "accounted", "unaccounted"):
                if not _is_nonnegative_int(row.get(field)):
                    errors.append(
                        "coverage.%s.%s must be a non-negative integer"
                        % (dimension, field)
                    )
            if all(_is_nonnegative_int(row.get(f)) for f in ("expected", "accounted", "unaccounted")):
                if row["unaccounted"] != 0:
                    errors.append(
                        "coverage.%s.unaccounted must be zero (found %d)"
                        % (dimension, row["unaccounted"])
                    )
                if row["accounted"] != row["expected"]:
                    errors.append(
                        "coverage.%s accounted %d of %d"
                        % (dimension, row["accounted"], row["expected"])
                    )
        actual_coverage_counts = {
            "price_skus": len(price_skus),
            "listings": len(listings),
            "jids": len(products_by_jid),
            "factory_items": len(factory_items),
        }
        for dimension, actual in actual_coverage_counts.items():
            row = coverage.get(dimension)
            if isinstance(row, dict) and _is_nonnegative_int(row.get("expected")):
                if row["expected"] != actual:
                    errors.append(
                        "coverage.%s.expected=%d but map contains %d"
                        % (dimension, row["expected"], actual)
                    )
        for field in _COVERAGE_ZERO_FIELDS:
            value = coverage.get(field)
            if not _is_nonnegative_int(value):
                errors.append("coverage.%s must be a non-negative integer" % field)
            elif value != 0:
                errors.append("coverage.%s must be zero (found %d)" % (field, value))
        if (
            _is_nonnegative_int(coverage.get("open_jid_conflicts"))
            and coverage.get("open_jid_conflicts") != blocking_conflicts
        ):
            errors.append(
                "coverage.open_jid_conflicts=%d but jid_conflicts has %d blocking row(s)"
                % (coverage["open_jid_conflicts"], blocking_conflicts)
            )
        if coverage.get("source_identity_sets_match") is not True:
            errors.append("coverage.source_identity_sets_match must be true")

        if errors:
            shown = errors[:20]
            suffix = "" if len(errors) <= len(shown) else "; ... %d more" % (
                len(errors) - len(shown)
            )
            raise IdentityMapError(
                "identity map failed validation: %s%s" % ("; ".join(shown), suffix)
            )
        return {
            "products": products,
            "products_by_jid": products_by_jid,
            "price_skus": price_skus,
            "listings": listings,
            "factory_items": factory_items,
            "factory_scopes": factory_scopes,
            "resolutions": resolutions,
            "resolution_product_keys": resolution_product_keys,
        }

    @property
    def contract(self):
        return self.data["contract"]

    @property
    def coverage(self):
        return self.data["coverage"]

    def _expanded_resolution(self, resolution):
        expanded = dict(resolution)
        expanded["factory_bindings"] = [
            {
                "binding": dict(binding),
                "factory_item": self.factory_items[binding["factory_item_key"]],
            }
            for binding in resolution.get("factory_bindings", [])
        ]
        return expanded

    def _operational_binding(self, binding):
        """Compact but fully qualified Factory binding for operational rows."""
        item = self.factory_items[binding["factory_item_key"]]
        return {
            "factory_item_key": item["factory_item_key"],
            "factory_scope_key": item["factory_scope_key"],
            "company_code": item["company_code"],
            "sap_schema": item["sap_schema"],
            "item_code": item["item_code"],
            "item_name": item["item_name"],
            "item_class": item["item_class"],
            "role": binding.get("role"),
            "primary_for_scope": binding.get("primary_for_scope"),
            "conversion_state": binding.get("conversion_state"),
            "factory_uom_per_listing_offer": binding.get(
                "factory_uom_per_listing_offer"
            ),
            "evidence_refs": [
                {
                    "source_id": evidence.get("source_id"),
                    "pointer": evidence.get("pointer"),
                    "evidence_kind": evidence.get("evidence_kind"),
                }
                for evidence in binding.get("evidence", [])
            ],
        }

    def enrich_listing(self, platform, listing_id):
        """Exact platform+listing-ID join for an operational source row.

        The method never consults product names. Unknown IDs and rows without an
        ID retain an explicit state and null identity fields.
        """
        normalized_platform = (
            platform.strip().lower() if isinstance(platform, str) else None
        )
        normalized_id = None
        if listing_id is not None and not isinstance(listing_id, bool):
            candidate = str(listing_id).strip()
            normalized_id = candidate or None
        observed_key = listing_key_for(normalized_platform, normalized_id)
        common = {
            "canonical_product_key": None,
            "jid": None,
            "price_sku_keys": [],
            "factory_bindings": [],
            "factory_mapping_state": None,
            "identity_resolution_id": None,
            "identity_dataset_version": self.contract["dataset_version"],
            "identity_map_sha256": self.map_sha256,
        }
        if normalized_id is None or normalized_platform is None:
            common.update(
                {
                    "listing_key": observed_key,
                    "identity_state": "missing_listing_id",
                }
            )
            return common
        listing = self.listings_by_platform_id.get(
            (normalized_platform, normalized_id)
        )
        if listing is None:
            common.update(
                {"listing_key": observed_key, "identity_state": "unmapped"}
            )
            return common
        resolution = self.resolutions_by_listing[listing["listing_key"]]
        product_key = self.resolution_product_keys[resolution["resolution_id"]]
        product = self.products[product_key]
        common.update(
            {
                "listing_key": listing["listing_key"],
                "canonical_product_key": product_key,
                "jid": product.get("jid"),
                "price_sku_keys": list(
                    listing.get("price_sku_keys") or [listing["price_sku_key"]]
                ),
                "factory_bindings": [
                    self._operational_binding(binding)
                    for binding in resolution.get("factory_bindings", [])
                ],
                "factory_mapping_state": resolution.get("factory_mapping_state"),
                "identity_resolution_id": resolution["resolution_id"],
                "identity_state": "mapped",
            }
        )
        return common

    def listing_targets(self, identifier):
        """Return exact ``(platform, listing_id)`` targets for any resolvable ID."""
        resolved = self.resolve(identifier)
        entity_type = resolved["entity_type"]
        if entity_type == "price_sku":
            members = resolved["members"]
        elif entity_type in ("product", "factory_item"):
            members = resolved["listings"]
        else:
            members = [resolved]
        targets = {
            (member["listing"]["platform"].lower(), member["listing"]["listing_id"])
            for member in members
        }
        return targets, resolved

    def _expanded_listing(self, listing, selected_price_sku_key=None):
        resolution = self.resolutions_by_listing.get(listing["listing_key"])
        price_sku_keys = listing.get("price_sku_keys") or [listing["price_sku_key"]]
        selected = selected_price_sku_key or listing["price_sku_key"]
        result = {
            "listing": listing,
            "price_sku": self.price_skus[selected],
            "price_skus": [self.price_skus[key] for key in price_sku_keys],
            "resolution": None,
            "product": None,
        }
        if resolution is not None:
            result["resolution"] = self._expanded_resolution(resolution)
            product_key = self.resolution_product_keys[resolution["resolution_id"]]
            result["product"] = self.products[product_key]
        return result

    def _resolved_product(self, product, requested_alias=None):
        product_key = _product_key(product)
        resolutions = self.resolutions_by_product.get(product_key, [])
        result = {
            "entity_type": "product",
            "product": product,
            "listings": [
                self._expanded_listing(self.listings[r["listing_key"]])
                for r in resolutions
            ],
        }
        if requested_alias is not None:
            result["requested_alias"] = requested_alias
        return result

    def _resolved_price_sku(self, price_sku):
        members = []
        for listing_key in price_sku.get("member_listing_keys", []):
            members.append(
                self._expanded_listing(
                    self.listings[listing_key],
                    selected_price_sku_key=price_sku["price_sku_key"],
                )
            )
        return {
            "entity_type": "price_sku",
            "price_sku": price_sku,
            "members": members,
        }

    def _resolved_listing(self, listing):
        result = self._expanded_listing(listing)
        result["entity_type"] = "listing"
        return result

    def _resolved_factory_item(self, factory_item):
        resolutions = self.resolutions_by_factory.get(
            factory_item["factory_item_key"], []
        )
        seen = set()
        listings = []
        for resolution in resolutions:
            listing_key = resolution["listing_key"]
            if listing_key in seen:
                continue
            seen.add(listing_key)
            listings.append(self._expanded_listing(self.listings[listing_key]))
        return {
            "entity_type": "factory_item",
            "factory_item": factory_item,
            "listings": listings,
        }

    def _qualified_listing_matches(self, identifier):
        matches = []
        for listing in self.data["listings"]:
            platform = listing["platform"]
            listing_id = listing["listing_id"]
            for separator in (":", "::", "/", "|"):
                prefix = platform + separator
                if identifier[: len(prefix)].lower() == prefix.lower() and identifier[
                    len(prefix) :
                ] == listing_id:
                    matches.append(listing)
                    break
        return matches

    def resolve(self, identifier):
        """Resolve only exact stable IDs, never display names."""
        if not isinstance(identifier, str) or not identifier.strip():
            raise IdentityNotFoundError("identifier must be non-empty")
        identifier = identifier.strip()
        matches = []
        requested_alias = self.jid_aliases.get(identifier)

        if identifier in self.products and requested_alias is None:
            matches.append(("product", self.products[identifier]))
        if requested_alias is not None:
            matches.append(
                (
                    "product",
                    self.products_by_jid[requested_alias["canonical_jid"]],
                )
            )
        elif identifier in self.products_by_jid:
            matches.append(("product", self.products_by_jid[identifier]))
        if identifier in self.price_skus:
            matches.append(("price_sku", self.price_skus[identifier]))
        for row in self.price_skus_by_code.get(identifier, []):
            matches.append(("price_sku", row))
        if identifier in self.listings:
            matches.append(("listing", self.listings[identifier]))
        for row in self._qualified_listing_matches(identifier):
            matches.append(("listing", row))
        if identifier in self.factory_items:
            matches.append(("factory_item", self.factory_items[identifier]))

        # A full key can also equal one of its accepted shorthand forms.  Collapse
        # those duplicate hits without hiding genuine cross-entity ambiguity.
        unique = []
        seen = set()
        key_fields = {
            "product": "product_key",
            "price_sku": "price_sku_key",
            "listing": "listing_key",
            "factory_item": "factory_item_key",
        }
        for kind, row in matches:
            row_key = _product_key(row) if kind == "product" else row[key_fields[kind]]
            identity = (kind, row_key)
            if identity not in seen:
                seen.add(identity)
                unique.append((kind, row))

        if not unique:
            raise IdentityNotFoundError(
                "no exact product identity for %r; use 'product search' for names"
                % identifier
            )
        if len(unique) > 1:
            candidates = [
                "%s:%s"
                % (
                    kind,
                    _product_key(row) if kind == "product" else row[key_fields[kind]],
                )
                for kind, row in unique
            ]
            raise IdentityAmbiguousError(identifier, candidates)

        kind, row = unique[0]
        if kind == "product":
            return self._resolved_product(row, requested_alias=requested_alias)
        if kind == "price_sku":
            return self._resolved_price_sku(row)
        if kind == "listing":
            return self._resolved_listing(row)
        return self._resolved_factory_item(row)

    @staticmethod
    def _matches_words(text, query_words):
        haystack = str(text or "").lower()
        return all(word in haystack for word in query_words)

    def search(self, text, limit=50):
        """Return human-review candidates; no result is treated as a join."""
        if not isinstance(text, str) or not text.strip():
            return []
        words = text.lower().split()
        candidates = []

        def add(kind, identifier, name, context, haystack):
            if self._matches_words(haystack, words):
                exact = text == identifier
                prefix = str(name or "").lower().startswith(text.lower())
                candidates.append(
                    (
                        0 if exact else (1 if prefix else 2),
                        kind,
                        str(name or "").lower(),
                        {
                            "entity_type": kind,
                            "identifier": identifier,
                            "name": name,
                            "context": context,
                            "candidate_only": True,
                        },
                    )
                )

        for row in self.data["products"]:
            product_key = _product_key(row)
            jid = row.get("jid")
            add(
                "product",
                product_key,
                row["canonical_name"],
                {"jid": jid, "state": row["state"]},
                " ".join(
                    value
                    for value in (product_key, jid, row["canonical_name"])
                    if value
                ),
            )
        for row in self.data["price_skus"]:
            add(
                "price_sku",
                row["price_sku_key"],
                row["display_name"],
                {
                    "source_namespace": row["source_namespace"],
                    "source_product_code": row["source_product_code"],
                    "state": row["state"],
                },
                " ".join(
                    (
                        row["price_sku_key"],
                        row["source_product_code"],
                        row["display_name"],
                    )
                ),
            )
        for row in self.data["listings"]:
            add(
                "listing",
                row["listing_key"],
                row["title"],
                {
                    "platform": row["platform"],
                    "listing_id": row["listing_id"],
                    "price_sku_key": row["price_sku_key"],
                    "state": row["state"],
                },
                " ".join(
                    (
                        row["listing_key"],
                        row["platform"],
                        row["listing_id"],
                        row["title"],
                    )
                ),
            )
        for row in self.data["factory_items"]:
            add(
                "factory_item",
                row["factory_item_key"],
                row["item_name"],
                {
                    "company_code": row["company_code"],
                    "sap_schema": row["sap_schema"],
                    "item_code": row["item_code"],
                    "state": row["state"],
                },
                " ".join(
                    (
                        row["factory_item_key"],
                        row["company_code"],
                        row["sap_schema"],
                        row["item_code"],
                        row["item_name"],
                    )
                ),
            )
        candidates.sort(key=lambda row: row[:3])
        return [row[3] for row in candidates[:limit]]

    def actual_counts(self):
        return {
            "products": len(self.data["products"]),
            "jids": sum(1 for row in self.data["products"] if row.get("jid")),
            "price_skus": len(self.data["price_skus"]),
            "listings": len(self.data["listings"]),
            "factory_items": len(self.data["factory_items"]),
            "resolutions": len(self.data["resolutions"]),
            "factory_bindings": sum(
                len(row.get("factory_bindings", []))
                for row in self.data["resolutions"]
            ),
        }

    def verification_result(self):
        return {
            "valid": True,
            "released": True,
            "map_path": self.path,
            "map_sha256": self.map_sha256,
            "attestation_path": self.attestation_path,
            "attestation_sha256": self.attestation_sha256,
            "contract": self.contract,
            "coverage": self.coverage,
            "actual_counts": self.actual_counts(),
        }
