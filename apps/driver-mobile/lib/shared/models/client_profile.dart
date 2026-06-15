/// Mirrors `ClientResponse` (backend `app/schemas/client.py`) — the shipper's
/// company/contact details for one carrier (tenant) relationship.
class ClientCompany {
  const ClientCompany({
    required this.id,
    required this.companyName,
    this.contactPerson,
    this.email,
    required this.phone,
    this.address,
    this.city,
    this.state,
    this.pincode,
  });

  factory ClientCompany.fromJson(Map<String, dynamic> json) {
    return ClientCompany(
      id: json['id'] as String,
      companyName: json['company_name'] as String,
      contactPerson: json['contact_person'] as String?,
      email: json['email'] as String?,
      phone: json['phone'] as String,
      address: json['address'] as String?,
      city: json['city'] as String?,
      state: json['state'] as String?,
      pincode: json['pincode'] as String?,
    );
  }

  final String id;
  final String companyName;
  final String? contactPerson;
  final String? email;
  final String phone;
  final String? address;
  final String? city;
  final String? state;
  final String? pincode;

  /// "123 Main St, Mumbai, Maharashtra 400001" — skips any unset parts.
  String? get fullAddress {
    final parts = [address, city, state, pincode].where((p) => p != null && p.isNotEmpty);
    return parts.isEmpty ? null : parts.join(', ');
  }
}

/// Mirrors `PortalCarrierLink` (backend `app/schemas/portal.py`) — one of the
/// shipper's carrier (tenant) relationships, returned by `GET /portal/me`.
class PortalCarrierLink {
  const PortalCarrierLink({
    required this.tenantId,
    required this.tenantName,
    required this.client,
  });

  factory PortalCarrierLink.fromJson(Map<String, dynamic> json) {
    return PortalCarrierLink(
      tenantId: json['tenant_id'] as String,
      tenantName: json['tenant_name'] as String,
      client: ClientCompany.fromJson(json['client'] as Map<String, dynamic>),
    );
  }

  final String tenantId;
  final String tenantName;
  final ClientCompany client;
}
