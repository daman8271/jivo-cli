
CREATE VIEW dbo.tbl_payments_view
 
AS
SELECT order_id, 'shipment_fee_amount' AS feenote, NULL AS promotion_id, shipment_fee_type AS feetype, shipment_fee_amount AS feeamt
FROM dbo.tbl_payments_line WHERE shipment_fee_type != ''
UNION all
SELECT order_id, 'order_fee_type', NULL, order_fee_type, order_fee_amount
FROM dbo.tbl_payments_line WHERE order_fee_type != ''
UNION all
SELECT order_id, 'price_type', NULL, price_type, price_amount
FROM dbo.tbl_payments_line WHERE price_type != ''
UNION all
SELECT order_id, 'item_related_fee_type', NULL, item_related_fee_type, item_related_fee_amount
FROM dbo.tbl_payments_line WHERE item_related_fee_type != ''
UNION all
SELECT order_id, 'misc_fee_amount', NULL, 'misc_fee_amount', misc_fee_amount
FROM dbo.tbl_payments_line WHERE abs(misc_fee_amount) > 0.00
UNION all
SELECT order_id, 'other_fee_reason_description', NULL, other_fee_reason_description, other_fee_amount
FROM dbo.tbl_payments_line WHERE other_fee_reason_description != ''
UNION all
SELECT order_id, 'promotion_type', promotion_id, promotion_type, promotion_amount
FROM dbo.tbl_payments_line WHERE promotion_type != ''
UNION all
SELECT order_id, 'direct_payment_type', NULL, direct_payment_type, direct_payment_amount
FROM dbo.tbl_payments_line WHERE direct_payment_type != ''
UNION all
SELECT order_id, 'other_amount', NULL, 'other', other_amount
FROM dbo.tbl_payments_line WHERE abs(other_amount) > 0.00;
