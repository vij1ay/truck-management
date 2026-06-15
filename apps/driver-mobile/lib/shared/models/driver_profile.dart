import 'truck_basic.dart';

/// Subset of `DriverMeResponse` (GET /drivers/me) needed by the driver app's
/// Profile and Vehicle Info screens.
class DriverProfile {
  const DriverProfile({
    required this.id,
    required this.fullName,
    required this.phone,
    this.email,
    this.address,
    required this.licenseNo,
    required this.licenseClass,
    required this.licenseExpiry,
    this.emergencyContactName,
    this.emergencyContactPhone,
    this.currentTruck,
  });

  factory DriverProfile.fromJson(Map<String, dynamic> json) {
    return DriverProfile(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      phone: json['phone'] as String,
      email: json['email'] as String?,
      address: json['address'] as String?,
      licenseNo: json['license_no'] as String,
      licenseClass: json['license_class'] as String,
      licenseExpiry: json['license_expiry'] as String,
      emergencyContactName: json['emergency_contact_name'] as String?,
      emergencyContactPhone: json['emergency_contact_phone'] as String?,
      currentTruck: json['current_truck'] == null
          ? null
          : TruckBasic.fromJson(json['current_truck'] as Map<String, dynamic>),
    );
  }

  final String id;
  final String fullName;
  final String phone;
  final String? email;
  final String? address;
  final String licenseNo;
  final String licenseClass;
  final String licenseExpiry;
  final String? emergencyContactName;
  final String? emergencyContactPhone;
  final TruckBasic? currentTruck;
}
