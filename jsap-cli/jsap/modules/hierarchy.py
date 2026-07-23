"""Employee Hierarchy module — HO org tree, Sales hierarchy, salary sessions.

READ-ONLY: GET only. Wraps every read endpoint in the Employee Hierarchy page
set (Hierarchy View, HO Hierarchy Master, Sales Hierarchy Master, Employee
Hierarchy): the HO org tree + flat admin grid, employee search & records,
departments / sub-departments, role types, custom-field defs/values, audit
logs, the Sales H1-H4 tree/rows/stats/lookups, and the safe salary-session
status check. No salary-session unlock, employee mutation, dept mutation, or
Excel import path is wrapped (those are password-gated / mutating writes).

Company scoping is session-based (the client selects the company at bootstrap),
so these endpoints take no company query param. Docs: docs/jsap/EmployeeHierarchy.md
"""

from __future__ import annotations

from .._reg import endpoint, group


def register(subparsers):
    g = group(subparsers, "hierarchy", "Employee/HO/Sales hierarchy + salary sessions")

    # -- HO org tree & flat grid (best structured / tabular sources) -------
    endpoint(
        g,
        "tree",
        path="/api/Hierarchy/GetHierarchyTree",
        help="Full HO org tree, one nested node per HOD "
        "(departments -> sub-HODs -> executives)",
    )

    endpoint(
        g,
        "flat",
        path="/api/Hierarchy/GetMasterFlatAdmin",
        help="Flat HO hierarchy rows (one per HOD/dept/sub-dept/sub-HOD/exec "
        "path) - best tabular source (~202 rows)",
    )

    # -- Employee search & single record -----------------------------------
    endpoint(
        g,
        "search",
        path="/api/Hierarchy/SearchEmployees",
        help="Search HO employees (term / role / active / page size)",
        params=[
            {
                "name": "searchTerm",
                "type": str,
                "required": False,
                "help": "Name/code search text",
            },
            {
                "name": "roleTypeId",
                "type": int,
                "required": False,
                "help": "Role filter: 1=HOD, 2=Sub-HOD, 3=Executive",
            },
            {
                "name": "isActive",
                "type": str,
                "required": False,
                "help": "Active filter: true or false",
            },
            {
                "name": "pageSize",
                "type": int,
                "required": False,
                "help": "Max rows to return (e.g. 500, 10000)",
            },
        ],
    )

    endpoint(
        g,
        "employee",
        path="/api/Hierarchy/GetEmployee/{employeeId}",
        help="Full employee record with reportsTo[] and directReports[]",
        params=[
            {
                "name": "employeeId",
                "type": int,
                "required": True,
                "positional": True,
                "path": True,
                "help": "Employee id",
            }
        ],
    )

    endpoint(
        g,
        "details",
        path="/HierarchyWeb/GetEmployeeHierarchyDetails",
        help="Employee record by id (same payload as `employee`; "
        "Employee Hierarchy page source)",
        params=[
            {
                "name": "id",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Employee id",
            }
        ],
    )

    # -- Unassigned / picker lists -----------------------------------------
    endpoint(
        g,
        "orphans",
        path="/api/Hierarchy/GetOrphanEmployees",
        help="Unassigned persons (no reporting relationship)",
    )

    endpoint(
        g,
        "hods",
        path="/api/Hierarchy/GetActiveHODs",
        help="Active HOD picker list (id, name, code)",
    )

    # -- Department masters -------------------------------------------------
    endpoint(
        g,
        "departments",
        path="/api/Hierarchy/GetDepartments",
        help="Department master, optionally with nested sub-departments",
        params=[
            {
                "name": "includeSubDepartments",
                "type": str,
                "required": False,
                "default": "true",
                "help": "Include sub-departments (true/false, default true)",
            }
        ],
    )

    endpoint(
        g,
        "subdepts",
        path="/api/Hierarchy/GetSubDepartments/{departmentId}",
        help="Sub-departments of one department",
        params=[
            {
                "name": "departmentId",
                "type": int,
                "required": True,
                "positional": True,
                "path": True,
                "help": "Department id",
            }
        ],
    )

    endpoint(
        g,
        "hod-depts",
        path="/api/Hierarchy/GetDepartmentsForHOD/{hodEmployeeId}",
        help="Departments owned by one HOD (with counts)",
        params=[
            {
                "name": "hodEmployeeId",
                "type": int,
                "required": True,
                "positional": True,
                "path": True,
                "help": "HOD employee id",
            }
        ],
    )

    endpoint(
        g,
        "subhods",
        path="/api/Hierarchy/GetSubHODsForEdit",
        help="Sub-HODs under one HOD",
        params=[
            {
                "name": "hodId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "HOD employee id",
            }
        ],
    )

    # -- Role types & per-employee extras ----------------------------------
    endpoint(
        g,
        "roles",
        path="/api/Hierarchy/GetRoleTypes",
        help="The 3 role types (HOD / Sub-HOD / Executive)",
    )

    endpoint(
        g,
        "extras",
        path="/api/Hierarchy/GetEmployeeModalExtras",
        help="Employee extras (gender/qualification/area/sikh flag)",
        params=[
            {
                "name": "employeeId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Employee id",
            }
        ],
    )

    # -- Custom-field definitions & values (currently empty) ---------------
    endpoint(
        g,
        "fields",
        path="/api/Hierarchy/GetCustomFields",
        help="Custom-field definitions (fieldId/name/type/required/options)",
    )

    endpoint(
        g,
        "custom-values",
        path="/api/Hierarchy/GetEmployeeCustomValues",
        help="Custom-field values (omit id = all employees)",
        params=[
            {
                "name": "employeeId",
                "type": int,
                "required": False,
                "help": "Employee id to scope to (omit for all)",
            }
        ],
    )

    # -- HO audit trail -----------------------------------------------------
    endpoint(
        g,
        "logs",
        path="/api/Hierarchy/GetAuditLogs",
        help="HO hierarchy audit trail (paged 30/page)",
        params=[
            {
                "name": "pageNumber",
                "type": int,
                "required": False,
                "default": 1,
                "help": "Page number (default 1)",
            },
            {
                "name": "pageSize",
                "type": int,
                "required": False,
                "default": 30,
                "help": "Rows per page (default 30)",
            },
            {
                "name": "searchTerm",
                "type": str,
                "required": False,
                "help": "Free-text search",
            },
            {
                "name": "actionType",
                "type": str,
                "required": False,
                "help": "Action filter (Create/Update/RoleChange/...)",
            },
        ],
    )

    # -- Salary session (safe status check only; never unlock from the CLI) -
    endpoint(
        g,
        "salary-session",
        path="/api/Hierarchy/GetSalarySessionData",
        help="Salary-session status (active flag + any live figures); "
        "reports active:false when no session",
    )

    endpoint(
        g,
        "salary-perms",
        path="/api/Hierarchy/GetEmployeesForSalaryPermission",
        help="All employees with their viewSalary permission flag",
    )

    # -- Sales hierarchy (field H1 -> H2 -> H3 -> H4 -> employee) ----------
    endpoint(
        g,
        "sales-tree",
        path="/HierarchyWeb/GetSalesHierarchyTree",
        help="Nested sales tree (H1->H2->H3->H4->group->employees)",
    )

    endpoint(
        g,
        "sales",
        path="/HierarchyWeb/GetSalesData",
        help="Flat sales rows (H1-H4 chain codes/names per employee)",
    )

    endpoint(
        g,
        "sales-stats",
        path="/HierarchyWeb/GetSalesStats",
        help="Sales level/employee counts (company-scoped)",
    )

    endpoint(
        g,
        "sales-lookups",
        path="/HierarchyWeb/GetSalesLookups",
        help="Sales lookups: states, groups, designations",
    )

    endpoint(
        g,
        "sales-employees",
        path="/HierarchyWeb/GetSalesEmployeeList",
        help="Sales employee picker list (id, name, code)",
    )

    endpoint(
        g,
        "sales-logs",
        path="/HierarchyWeb/GetSalesAuditLogs",
        help="Sales hierarchy audit trail (currently empty)",
        params=[
            {
                "name": "pageSize",
                "type": int,
                "required": False,
                "default": 100,
                "help": "Rows to return (default 100)",
            },
            {
                "name": "search",
                "type": str,
                "required": False,
                "default": "SalesHierarchy",
                "help": "Search text (default 'SalesHierarchy')",
            },
        ],
    )
