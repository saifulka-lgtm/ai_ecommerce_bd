# Manual Testing Checklist

Run through this after `python seed.py`, with the backend and frontend both
running, before demonstrating the project to anyone. Boxes map to the
automated tests in this folder where one exists (`pytest -v` to run them),
but a human should still eyeball the actual UI at least once.

## 1. Product discovery
- [ ] `Show me men's T-shirts` → only T-Shirts category products appear, as product cards (not just a text list).
- [ ] `আমাকে ১০০০ টাকার মধ্যে কালো টি-শার্ট দেখাও।` → only black T-shirts ≤ ৳1000.
- [ ] `Show me red shoes` → AI replies "not found" / offers another category. It must **not** show unrelated products.
- [ ] `What is the price of this product?` right after a search → resolves to a specific product from the results shown, with the real DB price.
- [ ] `প্রথমটার দাম কত?` after a Bangla search → resolves "the first one" correctly.

## 2. Stock & variants
- [ ] `Do you have this in XL?` → real stock number, not invented.
- [ ] Try adding more units than are in stock → AI/API refuses with a clear message, cart is unchanged.

## 3. Cart
- [ ] Add a product from a **product card** (grid) with a chosen size/color.
- [ ] Add the same product again → quantity increments, doesn't duplicate the line.
- [ ] `এটা L সাইজের ২টা কার্টে যোগ করো।` → adds 2 of the correct size, in Bangla.
- [ ] Open the cart drawer → totals match what the chat reported.
- [ ] Increase/decrease quantity with +/− in the cart drawer; remove an item.
- [ ] Cart total is free delivery above ৳2000 subtotal, ৳60 delivery below it.

## 4. Order flow
- [ ] `I want to place an order` with items in cart → AI asks for name/phone/address/payment.
- [ ] Provide the info across **multiple messages** → AI remembers what's already given and only asks for what's missing.
- [ ] Order is created: order number `DEMO-XXXX`, correct total, `payment_status = DEMO_SUCCESS`, `order_status = PENDING`.
- [ ] Checking out via the **cart drawer form** instead of chat also works end-to-end.
- [ ] `What is my order status?` → returns the real status.
- [ ] `Cancel order DEMO-XXXX` → order becomes CANCELLED and stock is restored (check Admin → Products).
- [ ] Try to cancel a DELIVERED order → refused with a clear message.

## 5. Bangla + English
- [ ] Every flow above works in **both** languages without the customer picking a language first.
- [ ] Mixed messages (Bangla sentence with a Latin size like `L`) still work.

## 6. Error handling
- [ ] Unknown product → graceful "not found", never a stack trace or invented product.
- [ ] Empty cart → "place order" is refused with a clear message, not a broken order.
- [ ] Stop the backend, refresh the frontend → clear error states, not a blank/broken page.

## 7. Admin panel (`/admin`)
- [ ] Wrong password → rejected. Cannot view any `/admin` page/API without logging in.
- [ ] Dashboard numbers match reality (compare against Orders tab / DB).
- [ ] Add a new product with 2+ variants → appears immediately on the storefront.
- [ ] Edit a variant's stock inline → storefront reflects it after a refresh.
- [ ] Deactivate a product → disappears from customer search, still visible in Admin.
- [ ] Change an order's status → customer-side `check_order_status` reflects the change.
- [ ] **AI Activity log** shows every chat message's tool call, arguments, and success/failure — this is the main demo feature, don't skip it.

## 8. Security sanity checks
- [ ] `.env` is not committed (check `.gitignore`); no secrets appear in frontend source.
- [ ] Admin API routes return 401 without a token (see automated `test_admin_endpoints_require_auth`).
- [ ] Order totals in the database always match `subtotal + delivery - discount`, even if you try to tamper with the request payload from devtools.
