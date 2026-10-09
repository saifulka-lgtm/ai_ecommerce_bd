"""
Product-discovery tools. Every one of these calls into product_service
(PostgreSQL) — none of them ever return data the AI made up.
"""
from typing import Any, Dict, Optional

from app.services import product_service
from app.tools.context import ToolContext
from app.tools import reference_resolver


def _ok(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": True, "data": data, "error": None}


def _err(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"success": False, "data": data, "error": message}


def search_products(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    products = product_service.search_products(
        ctx.db,
        query=args.get("query"),
        category=args.get("category"),
        color=args.get("color"),
        size=args.get("size"),
        min_price=args.get("min_price"),
        max_price=args.get("max_price"),
        on_sale=args.get("on_sale"),
        sort=args.get("sort"),
        limit=int(args.get("limit", 8)),
    )
    items = [product_service.to_list_item(p) for p in products]
    if not items:
        return _ok({"products": [], "count": 0})
    return _ok({"products": items, "count": len(items), "sorted_by": args.get("sort")})


def _resolve_product(args: Dict[str, Any], ctx: ToolContext):
    """Shared resolution: explicit product_id > ordinal reference ("the
    second one") > free-text name search > the single product last shown."""
    product_id = args.get("product_id")
    if product_id:
        try:
            return product_service.get_product(ctx.db, product_id)
        except product_service.ProductNotFoundError:
            pass

    ref_text = args.get("reference") or args.get("product_query") or ""
    shown = reference_resolver.resolve_from_last_shown(ctx, ref_text)
    if shown:
        try:
            return product_service.get_product(ctx.db, shown["id"])
        except product_service.ProductNotFoundError:
            pass

    query = args.get("product_query") or args.get("query")
    if query:
        matches = product_service.search_products(ctx.db, query=query, limit=1)
        if matches:
            return matches[0]

    single = reference_resolver.most_recently_shown_single(ctx)
    if single:
        try:
            return product_service.get_product(ctx.db, single["id"])
        except product_service.ProductNotFoundError:
            pass

    return None


def get_product_details(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    product = _resolve_product(args, ctx)
    if not product:
        return _err("Could not identify which product you mean — could you name it or search first?")

    detail = product_service.to_list_item(product)
    detail["description"] = product.description
    detail["sku"] = product.sku
    detail["variants"] = [
        {"size": v.size, "color": v.color, "stock": v.stock} for v in product.variants
    ]
    return _ok({"product": detail})


def check_product_stock(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    product = _resolve_product(args, ctx)
    if not product:
        return _err("Could not identify which product you mean.")

    size = args.get("size")
    color = args.get("color")

    if size or color:
        variant = None
        for v in product.variants:
            if size and v.size.lower() != str(size).lower():
                continue
            if color and v.color.lower() != str(color).lower():
                continue
            variant = v
            break
        if not variant:
            available = [{"size": v.size, "color": v.color, "stock": v.stock} for v in product.variants]
            return _err(
                f"No variant found for {product.name} in size={size or 'any'} color={color or 'any'}",
                data={"product_name": product.name, "available_variants": available},
            )
        return _ok({
            "product_name": product.name,
            "size": variant.size,
            "color": variant.color,
            "stock": variant.stock,
            "in_stock": variant.stock > 0,
        })

    variants = [{"size": v.size, "color": v.color, "stock": v.stock} for v in product.variants]
    return _ok({"product_name": product.name, "total_stock": product.total_stock, "variants": variants})


def get_product_variants(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    product = _resolve_product(args, ctx)
    if not product:
        return _err("Could not identify which product you mean.")

    return _ok({
        "product_name": product.name,
        "sizes": sorted({v.size for v in product.variants}),
        "colors": sorted({v.color for v in product.variants}),
        "variants": [{"size": v.size, "color": v.color, "stock": v.stock} for v in product.variants],
    })


def recommend_products(args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    category = args.get("category")
    products = product_service.search_products(ctx.db, category=category, limit=int(args.get("limit", 4)))
    in_stock = [p for p in products if p.total_stock > 0]
    items = [product_service.to_list_item(p) for p in (in_stock or products)]
    return _ok({"products": items, "count": len(items)})
