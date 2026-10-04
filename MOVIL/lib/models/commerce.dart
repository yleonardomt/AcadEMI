import '../core/utils/json_utils.dart';

class CartItem {
  CartItem({
    required this.courseId,
    required this.title,
    this.image,
    required this.teacher,
    this.category,
    required this.price,
    required this.isFree,
    this.levelLabel = '',
  });

  final int courseId;
  final String title, teacher, levelLabel;
  final String? image, category;
  final double price;
  final bool isFree;

  factory CartItem.fromJson(Map<String, dynamic> j) => CartItem(
        courseId: asInt(j['course_id']),
        title: asString(j['title']),
        image: asStringOrNull(j['image']),
        teacher: asString(j['teacher']),
        category: asStringOrNull(j['category']),
        price: asDouble(j['price']),
        isFree: asBool(j['is_free']),
        levelLabel: asString(j['level_label']),
      );
}

class CartData {
  CartData({
    required this.items,
    required this.subtotal,
    required this.discount,
    required this.total,
    this.discountLabel,
    this.couponCode,
    this.emiDiscount,
  });

  final List<CartItem> items;
  final double subtotal, discount, total;
  final String? discountLabel, couponCode;
  final double? emiDiscount;

  static CartData empty() => CartData(items: [], subtotal: 0, discount: 0, total: 0);

  factory CartData.fromResponse(Map<String, dynamic> j) {
    final c = (j['cart'] as Map<String, dynamic>?) ?? {};
    return CartData(
      items: asList(c['items']).map(CartItem.fromJson).toList(),
      subtotal: asDouble(c['subtotal']),
      discount: asDouble(c['discount']),
      total: asDouble(c['total']),
      discountLabel: asStringOrNull(c['discount_label']),
      couponCode: asStringOrNull(c['coupon_code']),
      emiDiscount: j['emi_discount'] == null ? null : asDouble(j['emi_discount']),
    );
  }
}

class PaymentItemLine {
  PaymentItemLine({required this.courseId, required this.title, required this.price, required this.finalPrice});

  final int courseId;
  final String title;
  final double price, finalPrice;

  factory PaymentItemLine.fromJson(Map<String, dynamic> j) => PaymentItemLine(
        courseId: asInt(j['course_id']),
        title: asString(j['title']),
        price: asDouble(j['price']),
        finalPrice: asDouble(j['final_price']),
      );
}

class PaymentSummary {
  PaymentSummary({
    required this.id,
    this.invoiceNumber,
    required this.amount,
    required this.discount,
    required this.total,
    required this.method,
    required this.methodLabel,
    required this.status,
    required this.statusLabel,
    this.createdAt,
    this.transactionId,
    this.coursesCount = 0,
    this.coupon,
    this.billingName = '',
    this.billingEmail = '',
    this.billingPhone = '',
    this.billingAddress = '',
    this.notes = '',
    this.cardLastFour,
    this.items = const [],
    this.pdfUrl,
  });

  final int id, coursesCount;
  final String? invoiceNumber, transactionId, coupon, cardLastFour, pdfUrl;
  final double amount, discount, total;
  final String method, methodLabel, status, statusLabel;
  final String billingName, billingEmail, billingPhone, billingAddress, notes;
  final DateTime? createdAt;
  final List<PaymentItemLine> items;

  factory PaymentSummary.fromJson(Map<String, dynamic> j) => PaymentSummary(
        id: asInt(j['id']),
        invoiceNumber: asStringOrNull(j['invoice_number']),
        amount: asDouble(j['amount']),
        discount: asDouble(j['discount']),
        total: asDouble(j['total']),
        method: asString(j['method']),
        methodLabel: asString(j['method_label']),
        status: asString(j['status']),
        statusLabel: asString(j['status_label']),
        createdAt: asDate(j['created_at']),
        transactionId: asStringOrNull(j['transaction_id']),
        coursesCount: asInt(j['courses_count']),
        coupon: asStringOrNull(j['coupon']),
        billingName: asString(j['billing_name']),
        billingEmail: asString(j['billing_email']),
        billingPhone: asString(j['billing_phone']),
        billingAddress: asString(j['billing_address']),
        notes: asString(j['notes']),
        cardLastFour: asStringOrNull(j['card_last_four']),
        items: asList(j['items']).map(PaymentItemLine.fromJson).toList(),
        pdfUrl: asStringOrNull(j['pdf_url']),
      );
}
