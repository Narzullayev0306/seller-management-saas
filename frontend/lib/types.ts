export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface RoleRef {
  code: string;
  name: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Me {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  organization_name: string;
  email_verified: boolean;
  status: string;
  roles: RoleRef[];
  permissions: string[];
}

export type UserStatus = "active" | "invited" | "suspended";

export interface Membership {
  organization_id: string;
  name: string;
  slug: string;
  plan: string;
  is_active: boolean;
  status: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  status: UserStatus;
  roles: string[];
  created_at: string;
}

export type ProductStatus = "active" | "inactive";
export type StockStatus = "in_stock" | "low_stock" | "out_of_stock";

export interface Product {
  id: string;
  name: string;
  sku: string;
  description: string | null;
  category: string;
  price: string;
  cost_price: string;
  stock_quantity: number;
  low_stock_threshold: number;
  status: ProductStatus;
  stock_status: StockStatus;
  image_url: string | null;
  created_at: string;
}

export interface ProductCreate {
  name: string;
  sku: string;
  description?: string;
  category: string;
  price: number;
  cost_price: number;
  stock_quantity: number;
  low_stock_threshold?: number;
  status?: ProductStatus;
  image_url?: string;
}

export interface ProductUpdate {
  name?: string;
  sku?: string;
  description?: string;
  category?: string;
  price?: number;
  cost_price?: number;
  stock_quantity?: number;
  low_stock_threshold?: number;
  status?: ProductStatus;
  image_url?: string;
}

export type SellerStatus = "active" | "inactive" | "suspended";

export interface Seller {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  status: SellerStatus;
  commission_rate: string;
  total_sales: string;
  total_orders: number;
  created_at: string;
}

export interface SellerCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  status?: SellerStatus;
  commission_rate: number;
  user_id?: string | null;
}

export interface SellerStats {
  total_sales: string;
  total_orders: number;
  total_commission: string;
  avg_order_value: string;
  recent_orders: Order[];
  performance: { period: string; sales: string }[];
}

export interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  address: string | null;
  total_orders: number;
  total_spent: string;
  created_at: string;
}

export interface CustomerCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  address?: string;
}

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled";

export type PaymentStatus = "pending" | "paid" | "partially_paid" | "refunded";

export interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export interface Order {
  id: string;
  order_number: string;
  seller_id: string | null;
  seller_name: string | null;
  customer_id: string;
  customer_name: string;
  created_by: string | null;
  created_by_name: string | null;
  status: OrderStatus;
  payment_status: PaymentStatus;
  subtotal: string;
  discount: string;
  tax: string;
  shipping_fee: string;
  total: string;
  items: OrderItem[];
  created_at: string;
}

export interface OrderCreate {
  seller_id?: string | null;
  customer_id: string;
  discount?: number;
  tax?: number;
  shipping_fee?: number;
  payment_status?: PaymentStatus;
  items: { product_id: string; quantity: number }[];
}

export interface OrderHistoryEntry {
  id: string;
  user_id: string | null;
  user_name: string | null;
  action: string;
  meta: Record<string, unknown> | null;
  created_at: string;
}

export type MovementType = "purchase" | "sale" | "adjustment" | "return";

export interface Movement {
  id: string;
  product_id: string;
  product_name: string;
  type: MovementType;
  quantity: number;
  reason: string | null;
  previous_stock: number | null;
  new_stock: number | null;
  reference_id: string | null;
  created_at: string;
}

export interface AdjustmentCreate {
  product_id: string;
  type: "purchase" | "adjustment";
  quantity: number;
  reason?: string;
}

export interface StockItem {
  id: string;
  name: string;
  sku: string;
  category: string;
  stock_quantity: number;
  low_stock_threshold: number;
  status: string;
  stock_status: StockStatus;
}

export interface Summary {
  revenue: string;
  orders_count: number;
  products_count: number;
  customers_count: number;
  active_sellers: number;
  low_stock_products: number;
  out_of_stock_products: number;
  avg_order_value: string;
  total_commission: string;
}

export interface SeriesPoint {
  date: string;
  value: string;
}

export interface TopItem {
  id: string;
  name: string;
  value: string;
  orders: number;
}

export interface CategorySales {
  category: string;
  value: string;
}

export interface RecentOrder {
  id: string;
  order_number: string;
  customer_name: string;
  total: string;
  status: string;
  created_at: string;
}

export interface LowStockProduct {
  id: string;
  name: string;
  sku: string;
  stock_quantity: number;
  low_stock_threshold: number;
}

export interface StatusCount {
  status: string;
  count: number;
}

export interface RevenueComparison {
  current: string;
  previous: string;
  change_percent: string;
}

export interface DashboardData {
  summary: Summary;
  revenue_over_time: SeriesPoint[];
  orders_over_time: SeriesPoint[];
  top_products: TopItem[];
  top_sellers: TopItem[];
  sales_by_category: CategorySales[];
  recent_orders: RecentOrder[];
  low_stock_products: LowStockProduct[];
  status_distribution: StatusCount[];
  revenue_comparison: RevenueComparison;
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  user_name: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  meta: Record<string, unknown> | null;
  created_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  read: boolean;
  created_at: string;
}

export type SupplierStatus = "active" | "inactive";

export interface Supplier {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  status: SupplierStatus;
  created_at: string;
}

export interface SupplierCreate {
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  status?: SupplierStatus;
}

export interface OrganizationSettings {
  id: string;
  name: string;
  slug: string;
  plan: string;
  logo_url: string | null;
  currency: string;
  timezone: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  created_at: string;
}

export interface Plan {
  code: string;
  name: string;
  price: string;
  description: string;
  features: string[];
  limits: Record<string, number | null>;
}

export interface BillingSummary {
  plan: string;
  plan_name: string;
  price: string;
  features: string[];
  limits: Record<string, number | null>;
  usage: Record<string, number>;
  subscription_status: string;
  period_end: string | null;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  plan: string;
  amount: string;
  currency: string;
  status: string;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
}

export interface OrganizationDomain {
  id: string;
  domain: string;
  status: "pending" | "verified";
  verification_token: string;
  verified_at: string | null;
  is_primary: boolean;
  created_at: string;
}

export type RangePreset = "today" | "7d" | "30d" | "90d" | "year";

export interface StorefrontProduct {
  id: string;
  name: string;
  category: string;
  price: string | number;
  stock_quantity: number;
  stock_status: StockStatus;
  image_url: string | null;
  brand_name: string | null;
  rating: number | null;
  review_count: number;
  featured: boolean;
}

export interface StorefrontBrand {
  id: string;
  name: string;
  logo_url: string | null;
  description: string | null;
  product_count: number;
}

export interface StorefrontReview {
  id: string;
  customer_name: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface StorefrontPricePoint {
  old_price: string;
  new_price: string;
  changed_at: string;
}

export interface StorefrontProductDetail extends StorefrontProduct {
  description: string | null;
  brand: { id: string; name: string; logo_url: string | null; description: string | null } | null;
  images: { id: string; url: string; position: number }[];
  reviews: StorefrontReview[];
  price_history: StorefrontPricePoint[];
}

export interface StorefrontCheckoutResult {
  order_id: string;
  order_number: string;
  status: string;
  total: string;
  items_count: number;
}

export interface StorefrontCatalogResponse {
  items: StorefrontProduct[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  categories: string[];
  brands: string[];
}

export interface CustomerMe {
  id: string;
  customer_id: string | null;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string | null;
  address: string | null;
  is_active: boolean;
}

export interface CustomerTokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CustomerRegisterInput {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  phone?: string;
}

export interface CustomerProfileUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  address?: string;
  current_password?: string;
  password?: string;
}

export interface CartItemRead {
  id: string;
  product_id: string;
  product_variant_id: string | null;
  name: string;
  sku: string;
  price: string | number;
  image_url: string | null;
  variant_name: string | null;
  variant_attributes: Record<string, string> | null;
  quantity: number;
  stock_quantity: number;
  subtotal: string | number;
  created_at: string;
}

export interface CartRead {
  cart_id: string;
  items: CartItemRead[];
  item_count: number;
  subtotal: string | number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  product_count: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryTreeNode extends Category {
  children: CategoryTreeNode[];
}

export interface CategoryCreate {
  name: string;
  slug?: string;
  parent_id?: string | null;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface CategoryUpdate {
  name?: string;
  slug?: string;
  parent_id?: string | null;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface ShippingMethod {
  id: string;
  name: string;
  description: string | null;
  price: string | number;
  min_order_amount: string | number | null;
  max_order_amount: string | number | null;
  estimated_delivery_days: number | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ShippingMethodCreate {
  name: string;
  description?: string;
  price: number;
  min_order_amount?: number;
  max_order_amount?: number;
  estimated_delivery_days?: number;
  is_active?: boolean;
  sort_order?: number;
}

export type ReturnStatus = "pending" | "approved" | "rejected" | "received" | "completed";

export interface ReturnRequest {
  id: string;
  order_id: string;
  order_item_id: string;
  product_id: string;
  product_variant_id: string | null;
  product_name: string;
  quantity: number;
  reason: string | null;
  condition: string;
  status: ReturnStatus;
  created_at: string;
  decided_at: string | null;
}

export type RefundStatus = "pending" | "processed" | "failed";

export interface Refund {
  id: string;
  order_id: string;
  order_number: string;
  return_request_id: string | null;
  payment_id: string | null;
  amount: string | number;
  reason: string | null;
  status: RefundStatus;
  created_at: string;
  processed_at: string | null;
}

export interface RefundCreate {
  order_id: string;
  amount: number;
  reason?: string;
  payment_id?: string;
}

export type PurchaseOrderStatus = "draft" | "ordered" | "received" | "cancelled";

export interface PurchaseOrderItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_cost: string | number;
  subtotal: string | number;
}

export interface PurchaseOrder {
  id: string;
  supplier_id: string | null;
  supplier_name: string | null;
  po_number: string;
  status: PurchaseOrderStatus;
  expected_date: string | null;
  notes: string | null;
  total: string | number;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  received_at: string | null;
  items: PurchaseOrderItem[];
}

export interface PurchaseOrderCreate {
  supplier_id?: string | null;
  expected_date?: string;
  notes?: string;
  items: { product_id: string; quantity: number; unit_cost: number }[];
}

export interface Webhook {
  id: string;
  name: string;
  url: string;
  secret: string;
  events: string[];
  is_active: boolean;
  last_delivered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WebhookCreate {
  name: string;
  url: string;
  events: string[];
  is_active?: boolean;
}

export interface WebhookUpdate {
  name?: string;
  url?: string;
  events?: string[];
  is_active?: boolean;
}

export interface WebhookDelivery {
  id: string;
  event_type: string;
  response_status: number | null;
  response_body: string | null;
  error: string | null;
  delivered_at: string | null;
  created_at: string;
}

export interface WebhookTestResult {
  ok: boolean;
  response_status: number | null;
  response_body: string | null;
  error: string | null;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
}

export interface ApiKeyWithSecret extends ApiKey {
  key: string;
}

export interface ApiKeyCreate {
  name: string;
  scopes: string[];
  expires_at?: string;
}

export interface ApiKeyUpdate {
  name?: string;
  scopes?: string[];
  is_active?: boolean;
  expires_at?: string | null;
}

export interface WishlistItemRead {
  id: string;
  product_id: string;
  product_variant_id: string | null;
  name: string;
  sku: string;
  price: string | number;
  image_url: string | null;
  variant_name: string | null;
  variant_attributes: Record<string, string> | null;
  in_stock: boolean;
  created_at: string;
}

export interface WishlistRead {
  wishlist_id: string;
  items: WishlistItemRead[];
  item_count: number;
}