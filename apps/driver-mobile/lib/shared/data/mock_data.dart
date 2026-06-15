import '../models/trip.dart';

/// Static sample data so every screen is reviewable without a backend
/// connection. Replace with real API calls once the gaps in
/// `mobile_app_design.md` (driver self-service endpoints) are closed.
class MockData {
  MockData._();

  static const driverName = 'Peter Williamson';
  static const driverPhone = '+1 987 654 3210';
  static const driverEmail = 'peter.williamson@email.com';
  static const driverLicenseNo = 'DL123456789';
  static const driverEmergencyContact = '+1 555 987 6543';
  static const driverAddress = '1141, Hemiltone Tower, New York, USA';
  static const driverRating = 4.8;
  static const driverTrips = 128;

  static final activeTrip = Trip(
    id: 'LD-2026-000123',
    loadNo: 'LD-2026-000123',
    title: 'Chemical Delivery',
    origin: 'New York, USA',
    destination: 'Chicago, USA',
    pickupDate: '20 May 2026',
    pickupTime: '11:30 AM',
    status: TripStatus.active,
    distanceKm: 125,
    etaLabel: '2h 30m',
    weightTonnes: 16.2,
    truckNumber: 'GTY 1024',
    truckModel: 'Scania R730',
    driverName: driverName,
    pickupAddress: '1141, Hemiltone Tower,\nNew York, USA',
    deliveryAddress: 'Neuro Chemical Factory,\nChicago, USA',
    departure: '20 May 2026, 11:30 AM',
  );

  static final trips = <Trip>[
    activeTrip,
    const Trip(
      id: 'LD-2026-000122',
      loadNo: 'LD-2026-000122',
      title: 'Raw Material Delivery',
      origin: 'Chicago, USA',
      destination: 'Detroit, USA',
      pickupDate: '20 May 2026',
      pickupTime: '08:45 AM',
      status: TripStatus.completed,
    ),
    const Trip(
      id: 'LD-2026-000124',
      loadNo: 'LD-2026-000124',
      title: 'Electric Items Delivery',
      origin: 'Boston, USA',
      destination: 'Philadelphia, USA',
      pickupDate: '21 May 2026',
      pickupTime: '09:30 AM',
      status: TripStatus.assigned,
    ),
    const Trip(
      id: 'LD-2026-000125',
      loadNo: 'LD-2026-000125',
      title: 'Pharma Delivery',
      origin: 'Atlanta, USA',
      destination: 'Miami, USA',
      pickupDate: '22 May 2026',
      pickupTime: '10:00 AM',
      status: TripStatus.pending,
    ),
  ];



  static const vehicleSpecs = <String, String>{
    'Truck Number': 'GTY 1024',
    'Brand': 'Scania',
    'Model': 'R730',
    'Max Load Capacity': '22.0 Tonnes',
    'Insurance Valid Till': '10 Oct 2026',
    'Fitness Valid Till': '15 Nov 2026',
    'Permit Valid Till': '20 Dec 2026',
  };
}
