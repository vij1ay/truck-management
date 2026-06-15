import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_ta.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('ta'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'TransTrack'**
  String get appTitle;

  /// No description provided for @onboardingChooseLanguage.
  ///
  /// In en, this message translates to:
  /// **'Choose your language'**
  String get onboardingChooseLanguage;

  /// No description provided for @onboardingChooseLanguageSubtitle.
  ///
  /// In en, this message translates to:
  /// **'You can change this later in Profile settings.'**
  String get onboardingChooseLanguageSubtitle;

  /// No description provided for @onboardingContinue.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get onboardingContinue;

  /// No description provided for @onboardingWhoAreYou.
  ///
  /// In en, this message translates to:
  /// **'Who are you?'**
  String get onboardingWhoAreYou;

  /// No description provided for @onboardingWhoAreYouSubtitle.
  ///
  /// In en, this message translates to:
  /// **'This helps us show you the right screens.'**
  String get onboardingWhoAreYouSubtitle;

  /// No description provided for @onboardingDriver.
  ///
  /// In en, this message translates to:
  /// **'I\'m a Driver'**
  String get onboardingDriver;

  /// No description provided for @onboardingDriverSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Manage trips, vehicles, and deliveries'**
  String get onboardingDriverSubtitle;

  /// No description provided for @onboardingClient.
  ///
  /// In en, this message translates to:
  /// **'I\'m a Client'**
  String get onboardingClient;

  /// No description provided for @onboardingClientSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Track shipments and invoices'**
  String get onboardingClientSubtitle;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navTrips.
  ///
  /// In en, this message translates to:
  /// **'Trips'**
  String get navTrips;

  /// No description provided for @navMap.
  ///
  /// In en, this message translates to:
  /// **'Map'**
  String get navMap;

  /// No description provided for @navNotifications.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get navNotifications;

  /// No description provided for @navProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// No description provided for @statusAssigned.
  ///
  /// In en, this message translates to:
  /// **'Assigned'**
  String get statusAssigned;

  /// No description provided for @statusActive.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get statusActive;

  /// No description provided for @statusPending.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get statusPending;

  /// No description provided for @statusCompleted.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get statusCompleted;

  /// No description provided for @statusCancelled.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get statusCancelled;

  /// No description provided for @statusInTransit.
  ///
  /// In en, this message translates to:
  /// **'IN TRANSIT'**
  String get statusInTransit;

  /// No description provided for @metricRemaining.
  ///
  /// In en, this message translates to:
  /// **'Remaining'**
  String get metricRemaining;

  /// No description provided for @metricEta.
  ///
  /// In en, this message translates to:
  /// **'ETA'**
  String get metricEta;

  /// No description provided for @viewAll.
  ///
  /// In en, this message translates to:
  /// **'View all'**
  String get viewAll;

  /// No description provided for @loginWelcomeBack.
  ///
  /// In en, this message translates to:
  /// **'Welcome Back'**
  String get loginWelcomeBack;

  /// No description provided for @loginSignInToContinue.
  ///
  /// In en, this message translates to:
  /// **'Sign in to continue'**
  String get loginSignInToContinue;

  /// No description provided for @loginEmailOrPhone.
  ///
  /// In en, this message translates to:
  /// **'Email or Phone'**
  String get loginEmailOrPhone;

  /// No description provided for @loginEmailHint.
  ///
  /// In en, this message translates to:
  /// **'Enter email or phone number'**
  String get loginEmailHint;

  /// No description provided for @loginPassword.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get loginPassword;

  /// No description provided for @loginPasswordHint.
  ///
  /// In en, this message translates to:
  /// **'Enter your password'**
  String get loginPasswordHint;

  /// No description provided for @loginRememberMe.
  ///
  /// In en, this message translates to:
  /// **'Remember me'**
  String get loginRememberMe;

  /// No description provided for @loginForgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot Password?'**
  String get loginForgotPassword;

  /// No description provided for @loginSignIn.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get loginSignIn;

  /// No description provided for @loginOr.
  ///
  /// In en, this message translates to:
  /// **'OR'**
  String get loginOr;

  /// No description provided for @loginSignInWithOtp.
  ///
  /// In en, this message translates to:
  /// **'Sign in with OTP'**
  String get loginSignInWithOtp;

  /// No description provided for @loginVersion.
  ///
  /// In en, this message translates to:
  /// **'Version {version}'**
  String loginVersion(String version);

  /// No description provided for @loginTagline.
  ///
  /// In en, this message translates to:
  /// **'Drive. Deliver. Trust.'**
  String get loginTagline;

  /// No description provided for @loginEnterCredentials.
  ///
  /// In en, this message translates to:
  /// **'Enter your email and password.'**
  String get loginEnterCredentials;

  /// No description provided for @dashboardGoodMorning.
  ///
  /// In en, this message translates to:
  /// **'Good Morning,'**
  String get dashboardGoodMorning;

  /// No description provided for @dashboardTodaysSummary.
  ///
  /// In en, this message translates to:
  /// **'Today\'s Summary'**
  String get dashboardTodaysSummary;

  /// No description provided for @dashboardActiveTrip.
  ///
  /// In en, this message translates to:
  /// **'Active Trip'**
  String get dashboardActiveTrip;

  /// No description provided for @dashboardContinueTrip.
  ///
  /// In en, this message translates to:
  /// **'Continue Trip'**
  String get dashboardContinueTrip;

  /// No description provided for @dashboardUpcomingAssignments.
  ///
  /// In en, this message translates to:
  /// **'Upcoming Assignments'**
  String get dashboardUpcomingAssignments;

  /// No description provided for @notificationsTitle.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notificationsTitle;

  /// No description provided for @notificationsMarkAsRead.
  ///
  /// In en, this message translates to:
  /// **'Mark as read'**
  String get notificationsMarkAsRead;

  /// No description provided for @notificationsRecentActivity.
  ///
  /// In en, this message translates to:
  /// **'Recent Activity'**
  String get notificationsRecentActivity;

  /// No description provided for @notificationsEmpty.
  ///
  /// In en, this message translates to:
  /// **'No recent activity.'**
  String get notificationsEmpty;

  /// No description provided for @notifNewTripTitle.
  ///
  /// In en, this message translates to:
  /// **'New Trip Assigned'**
  String get notifNewTripTitle;

  /// No description provided for @notifTripStartedTitle.
  ///
  /// In en, this message translates to:
  /// **'Trip Started'**
  String get notifTripStartedTitle;

  /// No description provided for @notifTripCompletedTitle.
  ///
  /// In en, this message translates to:
  /// **'Trip Completed'**
  String get notifTripCompletedTitle;

  /// No description provided for @notifTripCancelledTitle.
  ///
  /// In en, this message translates to:
  /// **'Trip Cancelled'**
  String get notifTripCancelledTitle;

  /// No description provided for @documentsTitle.
  ///
  /// In en, this message translates to:
  /// **'Documents'**
  String get documentsTitle;

  /// No description provided for @documentsTabVehicle.
  ///
  /// In en, this message translates to:
  /// **'Vehicle'**
  String get documentsTabVehicle;

  /// No description provided for @documentsTabDriver.
  ///
  /// In en, this message translates to:
  /// **'Driver'**
  String get documentsTabDriver;

  /// No description provided for @documentsTabTrip.
  ///
  /// In en, this message translates to:
  /// **'Trip'**
  String get documentsTabTrip;

  /// No description provided for @documentsEmpty.
  ///
  /// In en, this message translates to:
  /// **'No documents yet.'**
  String get documentsEmpty;

  /// No description provided for @documentsNoVehicle.
  ///
  /// In en, this message translates to:
  /// **'No vehicle assigned yet.'**
  String get documentsNoVehicle;

  /// No description provided for @vehicleInfoTitle.
  ///
  /// In en, this message translates to:
  /// **'Vehicle Information'**
  String get vehicleInfoTitle;

  /// No description provided for @vehicleInfoLastService.
  ///
  /// In en, this message translates to:
  /// **'Last Service: {date}'**
  String vehicleInfoLastService(String date);

  /// No description provided for @vehicleInfoPhotos.
  ///
  /// In en, this message translates to:
  /// **'Photos'**
  String get vehicleInfoPhotos;

  /// No description provided for @vehicleInfoNoPhotos.
  ///
  /// In en, this message translates to:
  /// **'No photos available for this vehicle yet.'**
  String get vehicleInfoNoPhotos;

  /// No description provided for @tripsTitle.
  ///
  /// In en, this message translates to:
  /// **'My Trips'**
  String get tripsTitle;

  /// No description provided for @tripsNoAssigned.
  ///
  /// In en, this message translates to:
  /// **'No assigned trips'**
  String get tripsNoAssigned;

  /// No description provided for @tripsNoActive.
  ///
  /// In en, this message translates to:
  /// **'No active trips'**
  String get tripsNoActive;

  /// No description provided for @tripsNoCompleted.
  ///
  /// In en, this message translates to:
  /// **'No completed trips'**
  String get tripsNoCompleted;

  /// No description provided for @tripsNoCancelled.
  ///
  /// In en, this message translates to:
  /// **'No cancelled trips'**
  String get tripsNoCancelled;

  /// No description provided for @tripsLoadError.
  ///
  /// In en, this message translates to:
  /// **'Couldn\'t load trips. Pull to refresh to try again.'**
  String get tripsLoadError;

  /// No description provided for @tripDetailsTitle.
  ///
  /// In en, this message translates to:
  /// **'Trip Details'**
  String get tripDetailsTitle;

  /// No description provided for @tripDetailsTruckInfo.
  ///
  /// In en, this message translates to:
  /// **'Truck: {truckNumber} ({truckModel})'**
  String tripDetailsTruckInfo(String truckNumber, String truckModel);

  /// No description provided for @tripDetailsDriverInfo.
  ///
  /// In en, this message translates to:
  /// **'Driver: {driverName}'**
  String tripDetailsDriverInfo(String driverName);

  /// No description provided for @tripDetailsClientLabel.
  ///
  /// In en, this message translates to:
  /// **'Client: {name}'**
  String tripDetailsClientLabel(String name);

  /// No description provided for @tripDetailsTabOverview.
  ///
  /// In en, this message translates to:
  /// **'Overview'**
  String get tripDetailsTabOverview;

  /// No description provided for @tripDetailsTabTimeline.
  ///
  /// In en, this message translates to:
  /// **'Timeline'**
  String get tripDetailsTabTimeline;

  /// No description provided for @tripDetailsTabNotes.
  ///
  /// In en, this message translates to:
  /// **'Notes'**
  String get tripDetailsTabNotes;

  /// No description provided for @tripDetailsPickupLocation.
  ///
  /// In en, this message translates to:
  /// **'Pickup Location'**
  String get tripDetailsPickupLocation;

  /// No description provided for @tripDetailsDeliveryLocation.
  ///
  /// In en, this message translates to:
  /// **'Delivery Location'**
  String get tripDetailsDeliveryLocation;

  /// No description provided for @tripDetailsDistance.
  ///
  /// In en, this message translates to:
  /// **'Distance'**
  String get tripDetailsDistance;

  /// No description provided for @tripDetailsLoadWeight.
  ///
  /// In en, this message translates to:
  /// **'Load Weight'**
  String get tripDetailsLoadWeight;

  /// No description provided for @tripDetailsDeparture.
  ///
  /// In en, this message translates to:
  /// **'Departure'**
  String get tripDetailsDeparture;

  /// No description provided for @tripDetailsViewRoute.
  ///
  /// In en, this message translates to:
  /// **'View Route'**
  String get tripDetailsViewRoute;

  /// No description provided for @tripDetailsMapPreviewNote.
  ///
  /// In en, this message translates to:
  /// **'Map preview is illustrative — see Active Trip (Map View) for the live route.'**
  String get tripDetailsMapPreviewNote;

  /// No description provided for @tripDetailsNoDocuments.
  ///
  /// In en, this message translates to:
  /// **'No documents for this trip yet.'**
  String get tripDetailsNoDocuments;

  /// No description provided for @tripDetailsSpecialInstructions.
  ///
  /// In en, this message translates to:
  /// **'Special Instructions'**
  String get tripDetailsSpecialInstructions;

  /// No description provided for @tripDetailsHazardousNote.
  ///
  /// In en, this message translates to:
  /// **'Handle with care — hazardous materials. Driver must wear PPE during loading/unloading.'**
  String get tripDetailsHazardousNote;

  /// No description provided for @tripDetailsStartTrip.
  ///
  /// In en, this message translates to:
  /// **'Start Trip'**
  String get tripDetailsStartTrip;

  /// No description provided for @tripDetailsMarkDelivered.
  ///
  /// In en, this message translates to:
  /// **'Mark Delivered'**
  String get tripDetailsMarkDelivered;

  /// No description provided for @tripDetailsCheckpointLoaded.
  ///
  /// In en, this message translates to:
  /// **'Loaded'**
  String get tripDetailsCheckpointLoaded;

  /// No description provided for @tripDetailsCheckpointReachedDestination.
  ///
  /// In en, this message translates to:
  /// **'Reached Destination'**
  String get tripDetailsCheckpointReachedDestination;

  /// No description provided for @tripDetailsCheckpointRecorded.
  ///
  /// In en, this message translates to:
  /// **'Checkpoint recorded'**
  String get tripDetailsCheckpointRecorded;

  /// No description provided for @timelineTripCreated.
  ///
  /// In en, this message translates to:
  /// **'Trip created'**
  String get timelineTripCreated;

  /// No description provided for @timelineConfirmedByDispatcher.
  ///
  /// In en, this message translates to:
  /// **'Confirmed by dispatcher'**
  String get timelineConfirmedByDispatcher;

  /// No description provided for @timelineTruckAndDriverAllocated.
  ///
  /// In en, this message translates to:
  /// **'Truck & driver allocated'**
  String get timelineTruckAndDriverAllocated;

  /// No description provided for @timelineTripStarted.
  ///
  /// In en, this message translates to:
  /// **'Trip started'**
  String get timelineTripStarted;

  /// No description provided for @timelineDelivered.
  ///
  /// In en, this message translates to:
  /// **'Delivered'**
  String get timelineDelivered;

  /// No description provided for @timelinePending.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get timelinePending;

  /// No description provided for @activeTripTitle.
  ///
  /// In en, this message translates to:
  /// **'Active Trip'**
  String get activeTripTitle;

  /// No description provided for @activeTripRefreshTooltip.
  ///
  /// In en, this message translates to:
  /// **'Refresh location & ETA'**
  String get activeTripRefreshTooltip;

  /// No description provided for @activeTripNextStep.
  ///
  /// In en, this message translates to:
  /// **'Next Step'**
  String get activeTripNextStep;

  /// No description provided for @activeTripReachPickupLocation.
  ///
  /// In en, this message translates to:
  /// **'Reach Pickup Location'**
  String get activeTripReachPickupLocation;

  /// No description provided for @activeTripReachedPickup.
  ///
  /// In en, this message translates to:
  /// **'Reached Pickup'**
  String get activeTripReachedPickup;

  /// No description provided for @activeTripSharingLocation.
  ///
  /// In en, this message translates to:
  /// **'Sharing live location'**
  String get activeTripSharingLocation;

  /// No description provided for @podTitle.
  ///
  /// In en, this message translates to:
  /// **'Proof of Delivery'**
  String get podTitle;

  /// No description provided for @podDeliveryPhoto.
  ///
  /// In en, this message translates to:
  /// **'Delivery Photo'**
  String get podDeliveryPhoto;

  /// No description provided for @podPhotoUploaded.
  ///
  /// In en, this message translates to:
  /// **'1 photo uploaded'**
  String get podPhotoUploaded;

  /// No description provided for @podNoPhotoYet.
  ///
  /// In en, this message translates to:
  /// **'No photo yet'**
  String get podNoPhotoYet;

  /// No description provided for @podRetake.
  ///
  /// In en, this message translates to:
  /// **'Retake'**
  String get podRetake;

  /// No description provided for @podReceiverSignature.
  ///
  /// In en, this message translates to:
  /// **'Receiver Signature'**
  String get podReceiverSignature;

  /// No description provided for @podTapToSign.
  ///
  /// In en, this message translates to:
  /// **'Tap to sign'**
  String get podTapToSign;

  /// No description provided for @podClear.
  ///
  /// In en, this message translates to:
  /// **'Clear'**
  String get podClear;

  /// No description provided for @podReceiverName.
  ///
  /// In en, this message translates to:
  /// **'Receiver Name'**
  String get podReceiverName;

  /// No description provided for @podReceiverNameHint.
  ///
  /// In en, this message translates to:
  /// **'Enter receiver name'**
  String get podReceiverNameHint;

  /// No description provided for @podRemarksOptional.
  ///
  /// In en, this message translates to:
  /// **'Remarks (Optional)'**
  String get podRemarksOptional;

  /// No description provided for @podRemarksHint.
  ///
  /// In en, this message translates to:
  /// **'Add any remarks about the delivery'**
  String get podRemarksHint;

  /// No description provided for @podSubmit.
  ///
  /// In en, this message translates to:
  /// **'Submit Proof of Delivery'**
  String get podSubmit;

  /// No description provided for @podSubmittedDemo.
  ///
  /// In en, this message translates to:
  /// **'Proof of delivery submitted (demo only).'**
  String get podSubmittedDemo;

  /// No description provided for @profileTitle.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profileTitle;

  /// No description provided for @profileVerified.
  ///
  /// In en, this message translates to:
  /// **'VERIFIED'**
  String get profileVerified;

  /// No description provided for @profilePhone.
  ///
  /// In en, this message translates to:
  /// **'Phone'**
  String get profilePhone;

  /// No description provided for @profileEmail.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get profileEmail;

  /// No description provided for @profileLicenseNo.
  ///
  /// In en, this message translates to:
  /// **'License No.'**
  String get profileLicenseNo;

  /// No description provided for @profileEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contact'**
  String get profileEmergencyContact;

  /// No description provided for @profileAddress.
  ///
  /// In en, this message translates to:
  /// **'Address'**
  String get profileAddress;

  /// No description provided for @profileVehicleInformation.
  ///
  /// In en, this message translates to:
  /// **'Vehicle Information'**
  String get profileVehicleInformation;

  /// No description provided for @profileDocuments.
  ///
  /// In en, this message translates to:
  /// **'Documents'**
  String get profileDocuments;

  /// No description provided for @profileSettings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get profileSettings;

  /// No description provided for @profileDarkMode.
  ///
  /// In en, this message translates to:
  /// **'Dark Mode'**
  String get profileDarkMode;

  /// No description provided for @profileLanguage.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get profileLanguage;

  /// No description provided for @profileLogOut.
  ///
  /// In en, this message translates to:
  /// **'Log Out'**
  String get profileLogOut;

  /// No description provided for @profileAvatarUpdated.
  ///
  /// In en, this message translates to:
  /// **'Profile picture updated.'**
  String get profileAvatarUpdated;

  /// No description provided for @profileAvatarUpdateFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to update profile picture.'**
  String get profileAvatarUpdateFailed;

  /// No description provided for @navShipments.
  ///
  /// In en, this message translates to:
  /// **'Shipments'**
  String get navShipments;

  /// No description provided for @navInvoices.
  ///
  /// In en, this message translates to:
  /// **'Invoices'**
  String get navInvoices;

  /// No description provided for @clientShipmentsTitle.
  ///
  /// In en, this message translates to:
  /// **'My Shipments'**
  String get clientShipmentsTitle;

  /// No description provided for @clientShipmentsEmpty.
  ///
  /// In en, this message translates to:
  /// **'No shipments found'**
  String get clientShipmentsEmpty;

  /// No description provided for @clientNewShipment.
  ///
  /// In en, this message translates to:
  /// **'New Shipment'**
  String get clientNewShipment;

  /// No description provided for @loadStatusAll.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get loadStatusAll;

  /// No description provided for @loadStatusDraft.
  ///
  /// In en, this message translates to:
  /// **'Draft'**
  String get loadStatusDraft;

  /// No description provided for @loadStatusConfirmed.
  ///
  /// In en, this message translates to:
  /// **'Confirmed'**
  String get loadStatusConfirmed;

  /// No description provided for @loadStatusAllocated.
  ///
  /// In en, this message translates to:
  /// **'Allocated'**
  String get loadStatusAllocated;

  /// No description provided for @loadStatusInTransit.
  ///
  /// In en, this message translates to:
  /// **'In Transit'**
  String get loadStatusInTransit;

  /// No description provided for @loadStatusDelivered.
  ///
  /// In en, this message translates to:
  /// **'Delivered'**
  String get loadStatusDelivered;

  /// No description provided for @loadStatusCancelled.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get loadStatusCancelled;

  /// No description provided for @bookingCarrier.
  ///
  /// In en, this message translates to:
  /// **'Carrier'**
  String get bookingCarrier;

  /// No description provided for @bookingOrigin.
  ///
  /// In en, this message translates to:
  /// **'Origin'**
  String get bookingOrigin;

  /// No description provided for @bookingDestination.
  ///
  /// In en, this message translates to:
  /// **'Destination'**
  String get bookingDestination;

  /// No description provided for @bookingPickupDate.
  ///
  /// In en, this message translates to:
  /// **'Pickup Date'**
  String get bookingPickupDate;

  /// No description provided for @bookingGoodsType.
  ///
  /// In en, this message translates to:
  /// **'Goods Type'**
  String get bookingGoodsType;

  /// No description provided for @bookingGoodsDescription.
  ///
  /// In en, this message translates to:
  /// **'Goods Description (optional)'**
  String get bookingGoodsDescription;

  /// No description provided for @bookingWeightKg.
  ///
  /// In en, this message translates to:
  /// **'Weight (kg)'**
  String get bookingWeightKg;

  /// No description provided for @bookingQuantity.
  ///
  /// In en, this message translates to:
  /// **'Quantity'**
  String get bookingQuantity;

  /// No description provided for @bookingTruckPreference.
  ///
  /// In en, this message translates to:
  /// **'Truck Preference (optional)'**
  String get bookingTruckPreference;

  /// No description provided for @bookingSpecialInstructions.
  ///
  /// In en, this message translates to:
  /// **'Special Instructions (optional)'**
  String get bookingSpecialInstructions;

  /// No description provided for @bookingNotes.
  ///
  /// In en, this message translates to:
  /// **'Notes (optional)'**
  String get bookingNotes;

  /// No description provided for @bookingSubmit.
  ///
  /// In en, this message translates to:
  /// **'Submit Booking Request'**
  String get bookingSubmit;

  /// No description provided for @bookingSubmitted.
  ///
  /// In en, this message translates to:
  /// **'Booking request submitted'**
  String get bookingSubmitted;

  /// No description provided for @bookingFieldRequired.
  ///
  /// In en, this message translates to:
  /// **'Required'**
  String get bookingFieldRequired;

  /// No description provided for @bookingNoCarriers.
  ///
  /// In en, this message translates to:
  /// **'No carrier accounts linked to your profile yet.'**
  String get bookingNoCarriers;

  /// No description provided for @clientShipmentDetailsTitle.
  ///
  /// In en, this message translates to:
  /// **'Shipment Details'**
  String get clientShipmentDetailsTitle;

  /// No description provided for @shipmentGoodsType.
  ///
  /// In en, this message translates to:
  /// **'Goods Type'**
  String get shipmentGoodsType;

  /// No description provided for @shipmentWeight.
  ///
  /// In en, this message translates to:
  /// **'Weight'**
  String get shipmentWeight;

  /// No description provided for @shipmentVolume.
  ///
  /// In en, this message translates to:
  /// **'Volume'**
  String get shipmentVolume;

  /// No description provided for @shipmentQuantity.
  ///
  /// In en, this message translates to:
  /// **'Quantity'**
  String get shipmentQuantity;

  /// No description provided for @shipmentFreightAmount.
  ///
  /// In en, this message translates to:
  /// **'Freight Amount'**
  String get shipmentFreightAmount;

  /// No description provided for @shipmentAdvanceAmount.
  ///
  /// In en, this message translates to:
  /// **'Advance Amount'**
  String get shipmentAdvanceAmount;

  /// No description provided for @shipmentBalanceAmount.
  ///
  /// In en, this message translates to:
  /// **'Balance Due'**
  String get shipmentBalanceAmount;

  /// No description provided for @shipmentExpectedDelivery.
  ///
  /// In en, this message translates to:
  /// **'Expected Delivery'**
  String get shipmentExpectedDelivery;

  /// No description provided for @shipmentActualDelivery.
  ///
  /// In en, this message translates to:
  /// **'Actual Delivery'**
  String get shipmentActualDelivery;

  /// No description provided for @shipmentTruckPreference.
  ///
  /// In en, this message translates to:
  /// **'Truck Preference'**
  String get shipmentTruckPreference;

  /// No description provided for @shipmentNoHistory.
  ///
  /// In en, this message translates to:
  /// **'No status history yet.'**
  String get shipmentNoHistory;

  /// No description provided for @shipmentNoDocuments.
  ///
  /// In en, this message translates to:
  /// **'No documents for this shipment yet.'**
  String get shipmentNoDocuments;

  /// No description provided for @notesLabel.
  ///
  /// In en, this message translates to:
  /// **'Notes'**
  String get notesLabel;

  /// No description provided for @clientInvoicesTitle.
  ///
  /// In en, this message translates to:
  /// **'My Invoices'**
  String get clientInvoicesTitle;

  /// No description provided for @clientInvoicesEmpty.
  ///
  /// In en, this message translates to:
  /// **'No invoices found'**
  String get clientInvoicesEmpty;

  /// No description provided for @invoiceStatusAll.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get invoiceStatusAll;

  /// No description provided for @invoiceStatusSent.
  ///
  /// In en, this message translates to:
  /// **'Sent'**
  String get invoiceStatusSent;

  /// No description provided for @invoiceStatusPartial.
  ///
  /// In en, this message translates to:
  /// **'Partially Paid'**
  String get invoiceStatusPartial;

  /// No description provided for @invoiceStatusPaid.
  ///
  /// In en, this message translates to:
  /// **'Paid'**
  String get invoiceStatusPaid;

  /// No description provided for @invoiceStatusOverdue.
  ///
  /// In en, this message translates to:
  /// **'Overdue'**
  String get invoiceStatusOverdue;

  /// No description provided for @invoiceSubtotal.
  ///
  /// In en, this message translates to:
  /// **'Subtotal'**
  String get invoiceSubtotal;

  /// No description provided for @invoiceTax.
  ///
  /// In en, this message translates to:
  /// **'Tax'**
  String get invoiceTax;

  /// No description provided for @invoiceTotal.
  ///
  /// In en, this message translates to:
  /// **'Total Amount'**
  String get invoiceTotal;

  /// No description provided for @invoicePaid.
  ///
  /// In en, this message translates to:
  /// **'Paid Amount'**
  String get invoicePaid;

  /// No description provided for @invoiceOutstanding.
  ///
  /// In en, this message translates to:
  /// **'Outstanding'**
  String get invoiceOutstanding;

  /// No description provided for @invoiceIssuedDate.
  ///
  /// In en, this message translates to:
  /// **'Issued Date'**
  String get invoiceIssuedDate;

  /// No description provided for @invoiceDueDate.
  ///
  /// In en, this message translates to:
  /// **'Due Date'**
  String get invoiceDueDate;

  /// No description provided for @invoiceDownloadPdf.
  ///
  /// In en, this message translates to:
  /// **'Download PDF'**
  String get invoiceDownloadPdf;

  /// No description provided for @invoiceDownloaded.
  ///
  /// In en, this message translates to:
  /// **'Invoice downloaded'**
  String get invoiceDownloaded;

  /// No description provided for @invoiceDownloadFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to download invoice'**
  String get invoiceDownloadFailed;

  /// No description provided for @invoicePaymentHistory.
  ///
  /// In en, this message translates to:
  /// **'Payment History'**
  String get invoicePaymentHistory;

  /// No description provided for @invoiceNoPayments.
  ///
  /// In en, this message translates to:
  /// **'No payments recorded yet.'**
  String get invoiceNoPayments;

  /// No description provided for @invoicePaymentReference.
  ///
  /// In en, this message translates to:
  /// **'Ref: {reference}'**
  String invoicePaymentReference(String reference);

  /// No description provided for @clientProfileTitle.
  ///
  /// In en, this message translates to:
  /// **'My Profile'**
  String get clientProfileTitle;

  /// No description provided for @clientCompanyName.
  ///
  /// In en, this message translates to:
  /// **'Company Name'**
  String get clientCompanyName;

  /// No description provided for @clientNoCarriers.
  ///
  /// In en, this message translates to:
  /// **'No carrier relationships found.'**
  String get clientNoCarriers;

  /// No description provided for @clientContactPerson.
  ///
  /// In en, this message translates to:
  /// **'Contact Person'**
  String get clientContactPerson;

  /// No description provided for @clientDashboardGreeting.
  ///
  /// In en, this message translates to:
  /// **'Welcome back,'**
  String get clientDashboardGreeting;

  /// No description provided for @clientShipmentSummary.
  ///
  /// In en, this message translates to:
  /// **'Shipment Summary'**
  String get clientShipmentSummary;

  /// No description provided for @clientRecentShipments.
  ///
  /// In en, this message translates to:
  /// **'Recent Shipments'**
  String get clientRecentShipments;

  /// No description provided for @clientTotalOutstanding.
  ///
  /// In en, this message translates to:
  /// **'Total Outstanding'**
  String get clientTotalOutstanding;

  /// No description provided for @shipmentOpenInMaps.
  ///
  /// In en, this message translates to:
  /// **'Open in Maps'**
  String get shipmentOpenInMaps;

  /// No description provided for @clientNotLinked.
  ///
  /// In en, this message translates to:
  /// **'Your account isn\'t linked to a customer portal yet. Please contact your carrier.'**
  String get clientNotLinked;

  /// No description provided for @clientGenericError.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Pull to refresh to try again.'**
  String get clientGenericError;

  /// No description provided for @clientAllCarriers.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get clientAllCarriers;

  /// No description provided for @clientEditShipment.
  ///
  /// In en, this message translates to:
  /// **'Edit Shipment'**
  String get clientEditShipment;

  /// No description provided for @clientSaveChanges.
  ///
  /// In en, this message translates to:
  /// **'Save Changes'**
  String get clientSaveChanges;

  /// No description provided for @clientCancelShipment.
  ///
  /// In en, this message translates to:
  /// **'Cancel Shipment'**
  String get clientCancelShipment;

  /// No description provided for @clientCancelConfirmMessage.
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to cancel this shipment request?'**
  String get clientCancelConfirmMessage;

  /// No description provided for @clientCancelReason.
  ///
  /// In en, this message translates to:
  /// **'Reason for cancellation'**
  String get clientCancelReason;

  /// No description provided for @clientCancelReasonHint.
  ///
  /// In en, this message translates to:
  /// **'Please provide at least 5 characters'**
  String get clientCancelReasonHint;

  /// No description provided for @clientShipmentCancelled.
  ///
  /// In en, this message translates to:
  /// **'Shipment cancelled'**
  String get clientShipmentCancelled;

  /// No description provided for @clientShipmentUpdated.
  ///
  /// In en, this message translates to:
  /// **'Shipment updated'**
  String get clientShipmentUpdated;

  /// No description provided for @clientUpdateFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to update shipment'**
  String get clientUpdateFailed;

  /// No description provided for @clientUploadDocument.
  ///
  /// In en, this message translates to:
  /// **'Upload Document'**
  String get clientUploadDocument;

  /// No description provided for @clientDocumentUploaded.
  ///
  /// In en, this message translates to:
  /// **'Document uploaded'**
  String get clientDocumentUploaded;

  /// No description provided for @clientDocumentUploadFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to upload document'**
  String get clientDocumentUploadFailed;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'hi', 'ta'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'ta':
      return AppLocalizationsTa();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
