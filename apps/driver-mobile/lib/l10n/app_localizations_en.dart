// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'TransTrack';

  @override
  String get onboardingChooseLanguage => 'Choose your language';

  @override
  String get onboardingChooseLanguageSubtitle =>
      'You can change this later in Profile settings.';

  @override
  String get onboardingContinue => 'Continue';

  @override
  String get onboardingWhoAreYou => 'Who are you?';

  @override
  String get onboardingWhoAreYouSubtitle =>
      'This helps us show you the right screens.';

  @override
  String get onboardingDriver => 'I\'m a Driver';

  @override
  String get onboardingDriverSubtitle =>
      'Manage trips, vehicles, and deliveries';

  @override
  String get onboardingClient => 'I\'m a Client';

  @override
  String get onboardingClientSubtitle => 'Track shipments and invoices';

  @override
  String get navHome => 'Home';

  @override
  String get navTrips => 'Trips';

  @override
  String get navMap => 'Map';

  @override
  String get navNotifications => 'Notifications';

  @override
  String get navProfile => 'Profile';

  @override
  String get statusAssigned => 'Assigned';

  @override
  String get statusActive => 'Active';

  @override
  String get statusPending => 'Pending';

  @override
  String get statusCompleted => 'Completed';

  @override
  String get statusCancelled => 'Cancelled';

  @override
  String get statusInTransit => 'IN TRANSIT';

  @override
  String get metricRemaining => 'Remaining';

  @override
  String get metricEta => 'ETA';

  @override
  String get viewAll => 'View all';

  @override
  String get loginWelcomeBack => 'Welcome Back';

  @override
  String get loginSignInToContinue => 'Sign in to continue';

  @override
  String get loginEmailOrPhone => 'Email or Phone';

  @override
  String get loginEmailHint => 'Enter email or phone number';

  @override
  String get loginPassword => 'Password';

  @override
  String get loginPasswordHint => 'Enter your password';

  @override
  String get loginRememberMe => 'Remember me';

  @override
  String get loginForgotPassword => 'Forgot Password?';

  @override
  String get loginSignIn => 'Sign In';

  @override
  String get loginOr => 'OR';

  @override
  String get loginSignInWithOtp => 'Sign in with OTP';

  @override
  String loginVersion(String version) {
    return 'Version $version';
  }

  @override
  String get loginTagline => 'Drive. Deliver. Trust.';

  @override
  String get loginEnterCredentials => 'Enter your email and password.';

  @override
  String get dashboardGoodMorning => 'Good Morning,';

  @override
  String get dashboardTodaysSummary => 'Today\'s Summary';

  @override
  String get dashboardActiveTrip => 'Active Trip';

  @override
  String get dashboardContinueTrip => 'Continue Trip';

  @override
  String get dashboardUpcomingAssignments => 'Upcoming Assignments';

  @override
  String get notificationsTitle => 'Notifications';

  @override
  String get notificationsMarkAsRead => 'Mark as read';

  @override
  String get notificationsRecentActivity => 'Recent Activity';

  @override
  String get notificationsEmpty => 'No recent activity.';

  @override
  String get notifNewTripTitle => 'New Trip Assigned';

  @override
  String get notifTripStartedTitle => 'Trip Started';

  @override
  String get notifTripCompletedTitle => 'Trip Completed';

  @override
  String get notifTripCancelledTitle => 'Trip Cancelled';

  @override
  String get documentsTitle => 'Documents';

  @override
  String get documentsTabVehicle => 'Vehicle';

  @override
  String get documentsTabDriver => 'Driver';

  @override
  String get documentsTabTrip => 'Trip';

  @override
  String get documentsEmpty => 'No documents yet.';

  @override
  String get documentsNoVehicle => 'No vehicle assigned yet.';

  @override
  String get vehicleInfoTitle => 'Vehicle Information';

  @override
  String vehicleInfoLastService(String date) {
    return 'Last Service: $date';
  }

  @override
  String get vehicleInfoPhotos => 'Photos';

  @override
  String get vehicleInfoNoPhotos => 'No photos available for this vehicle yet.';

  @override
  String get tripsTitle => 'My Trips';

  @override
  String get tripsNoAssigned => 'No assigned trips';

  @override
  String get tripsNoActive => 'No active trips';

  @override
  String get tripsNoCompleted => 'No completed trips';

  @override
  String get tripsNoCancelled => 'No cancelled trips';

  @override
  String get tripsLoadError =>
      'Couldn\'t load trips. Pull to refresh to try again.';

  @override
  String get tripDetailsTitle => 'Trip Details';

  @override
  String tripDetailsTruckInfo(String truckNumber, String truckModel) {
    return 'Truck: $truckNumber ($truckModel)';
  }

  @override
  String tripDetailsDriverInfo(String driverName) {
    return 'Driver: $driverName';
  }

  @override
  String tripDetailsClientLabel(String name) {
    return 'Client: $name';
  }

  @override
  String get tripDetailsTabOverview => 'Overview';

  @override
  String get tripDetailsTabTimeline => 'Timeline';

  @override
  String get tripDetailsTabNotes => 'Notes';

  @override
  String get tripDetailsPickupLocation => 'Pickup Location';

  @override
  String get tripDetailsDeliveryLocation => 'Delivery Location';

  @override
  String get tripDetailsDistance => 'Distance';

  @override
  String get tripDetailsLoadWeight => 'Load Weight';

  @override
  String get tripDetailsDeparture => 'Departure';

  @override
  String get tripDetailsViewRoute => 'View Route';

  @override
  String get tripDetailsMapPreviewNote =>
      'Map preview is illustrative — see Active Trip (Map View) for the live route.';

  @override
  String get tripDetailsNoDocuments => 'No documents for this trip yet.';

  @override
  String get tripDetailsSpecialInstructions => 'Special Instructions';

  @override
  String get tripDetailsHazardousNote =>
      'Handle with care — hazardous materials. Driver must wear PPE during loading/unloading.';

  @override
  String get tripDetailsStartTrip => 'Start Trip';

  @override
  String get tripDetailsMarkDelivered => 'Mark Delivered';

  @override
  String get tripDetailsCheckpointLoaded => 'Loaded';

  @override
  String get tripDetailsCheckpointReachedDestination => 'Reached Destination';

  @override
  String get tripDetailsCheckpointRecorded => 'Checkpoint recorded';

  @override
  String get timelineTripCreated => 'Trip created';

  @override
  String get timelineConfirmedByDispatcher => 'Confirmed by dispatcher';

  @override
  String get timelineTruckAndDriverAllocated => 'Truck & driver allocated';

  @override
  String get timelineTripStarted => 'Trip started';

  @override
  String get timelineDelivered => 'Delivered';

  @override
  String get timelinePending => 'Pending';

  @override
  String get activeTripTitle => 'Active Trip';

  @override
  String get activeTripRefreshTooltip => 'Refresh location & ETA';

  @override
  String get activeTripNextStep => 'Next Step';

  @override
  String get activeTripReachPickupLocation => 'Reach Pickup Location';

  @override
  String get activeTripReachedPickup => 'Reached Pickup';

  @override
  String get activeTripSharingLocation => 'Sharing live location';

  @override
  String get podTitle => 'Proof of Delivery';

  @override
  String get podDeliveryPhoto => 'Delivery Photo';

  @override
  String get podPhotoUploaded => '1 photo uploaded';

  @override
  String get podNoPhotoYet => 'No photo yet';

  @override
  String get podRetake => 'Retake';

  @override
  String get podReceiverSignature => 'Receiver Signature';

  @override
  String get podTapToSign => 'Tap to sign';

  @override
  String get podClear => 'Clear';

  @override
  String get podReceiverName => 'Receiver Name';

  @override
  String get podReceiverNameHint => 'Enter receiver name';

  @override
  String get podRemarksOptional => 'Remarks (Optional)';

  @override
  String get podRemarksHint => 'Add any remarks about the delivery';

  @override
  String get podSubmit => 'Submit Proof of Delivery';

  @override
  String get podSubmittedDemo => 'Proof of delivery submitted (demo only).';

  @override
  String get profileTitle => 'Profile';

  @override
  String get profileVerified => 'VERIFIED';

  @override
  String get profilePhone => 'Phone';

  @override
  String get profileEmail => 'Email';

  @override
  String get profileLicenseNo => 'License No.';

  @override
  String get profileEmergencyContact => 'Emergency Contact';

  @override
  String get profileAddress => 'Address';

  @override
  String get profileVehicleInformation => 'Vehicle Information';

  @override
  String get profileDocuments => 'Documents';

  @override
  String get profileSettings => 'Settings';

  @override
  String get profileDarkMode => 'Dark Mode';

  @override
  String get profileLanguage => 'Language';

  @override
  String get profileLogOut => 'Log Out';

  @override
  String get profileAvatarUpdated => 'Profile picture updated.';

  @override
  String get profileAvatarUpdateFailed => 'Failed to update profile picture.';

  @override
  String get navShipments => 'Shipments';

  @override
  String get navInvoices => 'Invoices';

  @override
  String get clientShipmentsTitle => 'My Shipments';

  @override
  String get clientShipmentsEmpty => 'No shipments found';

  @override
  String get clientNewShipment => 'New Shipment';

  @override
  String get loadStatusAll => 'All';

  @override
  String get loadStatusDraft => 'Draft';

  @override
  String get loadStatusConfirmed => 'Confirmed';

  @override
  String get loadStatusAllocated => 'Allocated';

  @override
  String get loadStatusInTransit => 'In Transit';

  @override
  String get loadStatusDelivered => 'Delivered';

  @override
  String get loadStatusCancelled => 'Cancelled';

  @override
  String get bookingCarrier => 'Carrier';

  @override
  String get bookingOrigin => 'Origin';

  @override
  String get bookingDestination => 'Destination';

  @override
  String get bookingPickupDate => 'Pickup Date';

  @override
  String get bookingGoodsType => 'Goods Type';

  @override
  String get bookingGoodsDescription => 'Goods Description (optional)';

  @override
  String get bookingWeightKg => 'Weight (kg)';

  @override
  String get bookingQuantity => 'Quantity';

  @override
  String get bookingTruckPreference => 'Truck Preference (optional)';

  @override
  String get bookingSpecialInstructions => 'Special Instructions (optional)';

  @override
  String get bookingNotes => 'Notes (optional)';

  @override
  String get bookingSubmit => 'Submit Booking Request';

  @override
  String get bookingSubmitted => 'Booking request submitted';

  @override
  String get bookingFieldRequired => 'Required';

  @override
  String get bookingNoCarriers =>
      'No carrier accounts linked to your profile yet.';

  @override
  String get clientShipmentDetailsTitle => 'Shipment Details';

  @override
  String get shipmentGoodsType => 'Goods Type';

  @override
  String get shipmentWeight => 'Weight';

  @override
  String get shipmentVolume => 'Volume';

  @override
  String get shipmentQuantity => 'Quantity';

  @override
  String get shipmentFreightAmount => 'Freight Amount';

  @override
  String get shipmentAdvanceAmount => 'Advance Amount';

  @override
  String get shipmentBalanceAmount => 'Balance Due';

  @override
  String get shipmentExpectedDelivery => 'Expected Delivery';

  @override
  String get shipmentActualDelivery => 'Actual Delivery';

  @override
  String get shipmentTruckPreference => 'Truck Preference';

  @override
  String get shipmentNoHistory => 'No status history yet.';

  @override
  String get shipmentNoDocuments => 'No documents for this shipment yet.';

  @override
  String get notesLabel => 'Notes';

  @override
  String get clientInvoicesTitle => 'My Invoices';

  @override
  String get clientInvoicesEmpty => 'No invoices found';

  @override
  String get invoiceStatusAll => 'All';

  @override
  String get invoiceStatusSent => 'Sent';

  @override
  String get invoiceStatusPartial => 'Partially Paid';

  @override
  String get invoiceStatusPaid => 'Paid';

  @override
  String get invoiceStatusOverdue => 'Overdue';

  @override
  String get invoiceSubtotal => 'Subtotal';

  @override
  String get invoiceTax => 'Tax';

  @override
  String get invoiceTotal => 'Total Amount';

  @override
  String get invoicePaid => 'Paid Amount';

  @override
  String get invoiceOutstanding => 'Outstanding';

  @override
  String get invoiceIssuedDate => 'Issued Date';

  @override
  String get invoiceDueDate => 'Due Date';

  @override
  String get invoiceDownloadPdf => 'Download PDF';

  @override
  String get invoiceDownloaded => 'Invoice downloaded';

  @override
  String get invoiceDownloadFailed => 'Failed to download invoice';

  @override
  String get invoicePaymentHistory => 'Payment History';

  @override
  String get invoiceNoPayments => 'No payments recorded yet.';

  @override
  String invoicePaymentReference(String reference) {
    return 'Ref: $reference';
  }

  @override
  String get clientProfileTitle => 'My Profile';

  @override
  String get clientCompanyName => 'Company Name';

  @override
  String get clientNoCarriers => 'No carrier relationships found.';

  @override
  String get clientContactPerson => 'Contact Person';

  @override
  String get clientDashboardGreeting => 'Welcome back,';

  @override
  String get clientShipmentSummary => 'Shipment Summary';

  @override
  String get clientRecentShipments => 'Recent Shipments';

  @override
  String get clientTotalOutstanding => 'Total Outstanding';

  @override
  String get shipmentOpenInMaps => 'Open in Maps';

  @override
  String get clientNotLinked =>
      'Your account isn\'t linked to a customer portal yet. Please contact your carrier.';

  @override
  String get clientGenericError =>
      'Something went wrong. Pull to refresh to try again.';

  @override
  String get clientAllCarriers => 'All';

  @override
  String get clientEditShipment => 'Edit Shipment';

  @override
  String get clientSaveChanges => 'Save Changes';

  @override
  String get clientCancelShipment => 'Cancel Shipment';

  @override
  String get clientCancelConfirmMessage =>
      'Are you sure you want to cancel this shipment request?';

  @override
  String get clientCancelReason => 'Reason for cancellation';

  @override
  String get clientCancelReasonHint => 'Please provide at least 5 characters';

  @override
  String get clientShipmentCancelled => 'Shipment cancelled';

  @override
  String get clientShipmentUpdated => 'Shipment updated';

  @override
  String get clientUpdateFailed => 'Failed to update shipment';

  @override
  String get clientUploadDocument => 'Upload Document';

  @override
  String get clientDocumentUploaded => 'Document uploaded';

  @override
  String get clientDocumentUploadFailed => 'Failed to upload document';
}
