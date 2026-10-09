from typing import Any, Dict, Optional

from app.services import cart_service, product_service
from app.tools.context import ToolContext
from app.tools.product_tools import _resolve_product, _ok, _err


def _resolve_variant(args: Dict[str, Any], ctx: ToolContext):
    variant_id = args.get("variant_id")
    if variant_id:
        try:
            return product_service.get_variant(ctx.db, variant_id), None
        except product_service.VariantNotFoundError:
            return None, "That product variant no longer exists."

    product = _resolve_product(args, ctx)
    if not product:
        return None, "Could not identify which product you mean."

    size = args.get("size")
    color = args.get("color")

    candidates = product.variants
    if size:
        candidates = [v for v in candidates if v.size.lower() == str(size).lower()]
    if color:
        candidates = [v for v in candidates if v.color.lower() == str(color).lower()]

    if len(candidates) == 1:
        return candidates[0], None

    if len(candidates) == 0:
        available = [{"size": v.size, "color": v.color, "stock": v.stock} for v in product.variants]
        return None, {
            "message": f"No matching size/color for {product.name}.",
            "product_name": product.name,
            "available_variants": available,
        }

    # multiple matches -> need the customer to disambiguate
    available = [{"size": v.size, "color": v.color, "stock": v.stock} for v in candidates]
    return None, {
        "message": f"Which size and color of {product.name} did you want?",
        "product_name": product.name,
        "available_variants": available,
    }


def add_to_cart(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    variant, err = _resolve_variant(args, ctx)
    if not variant:
        if isinstance(err, dict):
            return _err(err["message"], data=err)
        return _err(err or "Could not resolve the product/variant.")

    quantity = int(args.get("quantity", 1))
    try:
        cart_service.add_to_cart(ctx.db, ctx.session_id, variant.id, quantity)
    except cart_service.InsufficientStockError as e:
        return _err(str(e))

    totals = cart_service.calculate_cart_total(ctx.db, ctx.session_id)
    return _ok(totals)


def remove_from_cart(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    variant, err = _resolve_variant(args, ctx)
    if not variant:
        if isinstance(err, dict):
            return _err(err["message"], data=err)
        return _err(err or "Could not resolve the product/variant.")

    try:
        cart_service.remove_from_cart(ctx.db, ctx.session_id, variant.id)
    except cart_service.CartItemNotFoundError:
        return _err("That item isn't in your cart.")

    totals = cart_service.calculate_cart_total(ctx.db, ctx.session_id)
    return _ok(totals)


def update_cart_quantity(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    variant, err = _resolve_variant(args, ctx)
    if not variant:
        if isinstance(err, dict):
            return _err(err["message"], data=err)
        return _err(err or "Could not resolve the product/variant.")

    quantity = int(args.get("quantity", 1))
    try:
        cart_service.update_cart_quantity(ctx.db, ctx.session_id, variant.id, quantity)
    except cart_service.CartItemNotFoundError:
        return _err("That item isn't in your cart.")
    except cart_service.InsufficientStockError as e:
        return _err(str(e))

    totals = cart_service.calculate_cart_total(ctx.db, ctx.session_id)
    return _ok(totals)


def get_cart(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    totals = cart_service.calculate_cart_total(ctx.db, ctx.session_id)
    return _ok(totals)


def calculate_cart_total(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    totals = cart_service.calculate_cart_total(ctx.db, ctx.session_id)
    return _ok(totals)
