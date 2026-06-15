// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'ट्रांसट्रैक';

  @override
  String get onboardingChooseLanguage => 'अपनी भाषा चुनें';

  @override
  String get onboardingChooseLanguageSubtitle =>
      'आप इसे बाद में प्रोफ़ाइल सेटिंग्स में बदल सकते हैं।';

  @override
  String get onboardingContinue => 'जारी रखें';

  @override
  String get onboardingWhoAreYou => 'आप कौन हैं?';

  @override
  String get onboardingWhoAreYouSubtitle =>
      'इससे हमें आपको सही स्क्रीन दिखाने में मदद मिलती है।';

  @override
  String get onboardingDriver => 'मैं एक ड्राइवर हूं';

  @override
  String get onboardingDriverSubtitle =>
      'ट्रिप्स, वाहन और डिलीवरी प्रबंधित करें';

  @override
  String get onboardingClient => 'मैं एक क्लाइंट हूं';

  @override
  String get onboardingClientSubtitle => 'शिपमेंट और इनवॉइस ट्रैक करें';

  @override
  String get navHome => 'होम';

  @override
  String get navTrips => 'ट्रिप्स';

  @override
  String get navMap => 'मैप';

  @override
  String get navNotifications => 'सूचनाएं';

  @override
  String get navProfile => 'प्रोफ़ाइल';

  @override
  String get statusAssigned => 'असाइन किया गया';

  @override
  String get statusActive => 'सक्रिय';

  @override
  String get statusPending => 'लंबित';

  @override
  String get statusCompleted => 'पूर्ण';

  @override
  String get statusCancelled => 'रद्द';

  @override
  String get statusInTransit => 'ट्रांज़िट में';

  @override
  String get metricRemaining => 'शेष';

  @override
  String get metricEta => 'ईटीए';

  @override
  String get viewAll => 'सभी देखें';

  @override
  String get loginWelcomeBack => 'वापसी पर स्वागत है';

  @override
  String get loginSignInToContinue => 'जारी रखने के लिए साइन इन करें';

  @override
  String get loginEmailOrPhone => 'ईमेल या फ़ोन';

  @override
  String get loginEmailHint => 'ईमेल या फ़ोन नंबर दर्ज करें';

  @override
  String get loginPassword => 'पासवर्ड';

  @override
  String get loginPasswordHint => 'अपना पासवर्ड दर्ज करें';

  @override
  String get loginRememberMe => 'मुझे याद रखें';

  @override
  String get loginForgotPassword => 'पासवर्ड भूल गए?';

  @override
  String get loginSignIn => 'साइन इन करें';

  @override
  String get loginOr => 'या';

  @override
  String get loginSignInWithOtp => 'ओटीपी से साइन इन करें';

  @override
  String loginVersion(String version) {
    return 'वर्शन $version';
  }

  @override
  String get loginTagline => 'चलाएं। पहुंचाएं। भरोसा।';

  @override
  String get loginEnterCredentials => 'अपना ईमेल और पासवर्ड दर्ज करें।';

  @override
  String get dashboardGoodMorning => 'सुप्रभात,';

  @override
  String get dashboardTodaysSummary => 'आज का सारांश';

  @override
  String get dashboardActiveTrip => 'सक्रिय ट्रिप';

  @override
  String get dashboardContinueTrip => 'ट्रिप जारी रखें';

  @override
  String get dashboardUpcomingAssignments => 'आने वाले असाइनमेंट';

  @override
  String get notificationsTitle => 'सूचनाएं';

  @override
  String get notificationsMarkAsRead => 'पढ़ा हुआ चिह्नित करें';

  @override
  String get notificationsRecentActivity => 'हाल की गतिविधि';

  @override
  String get notificationsEmpty => 'कोई हाल की गतिविधि नहीं है।';

  @override
  String get notifNewTripTitle => 'नई ट्रिप असाइन की गई';

  @override
  String get notifTripStartedTitle => 'ट्रिप शुरू हुई';

  @override
  String get notifTripCompletedTitle => 'ट्रिप पूरी हुई';

  @override
  String get notifTripCancelledTitle => 'ट्रिप रद्द की गई';

  @override
  String get documentsTitle => 'दस्तावेज़';

  @override
  String get documentsTabVehicle => 'वाहन';

  @override
  String get documentsTabDriver => 'ड्राइवर';

  @override
  String get documentsTabTrip => 'ट्रिप';

  @override
  String get documentsEmpty => 'अभी कोई दस्तावेज़ नहीं है।';

  @override
  String get documentsNoVehicle => 'अभी तक कोई वाहन असाइन नहीं किया गया है।';

  @override
  String get vehicleInfoTitle => 'वाहन की जानकारी';

  @override
  String vehicleInfoLastService(String date) {
    return 'अंतिम सर्विस: $date';
  }

  @override
  String get vehicleInfoPhotos => 'तस्वीरें';

  @override
  String get vehicleInfoNoPhotos =>
      'इस वाहन के लिए अभी कोई तस्वीर उपलब्ध नहीं है।';

  @override
  String get tripsTitle => 'मेरी ट्रिप्स';

  @override
  String get tripsNoAssigned => 'कोई असाइन की गई ट्रिप नहीं';

  @override
  String get tripsNoActive => 'कोई सक्रिय ट्रिप नहीं';

  @override
  String get tripsNoCompleted => 'कोई पूर्ण ट्रिप नहीं';

  @override
  String get tripsNoCancelled => 'कोई रद्द ट्रिप नहीं';

  @override
  String get tripsLoadError =>
      'ट्रिप्स लोड नहीं हो सकीं। पुनः प्रयास करने के लिए रिफ्रेश करें।';

  @override
  String get tripDetailsTitle => 'ट्रिप विवरण';

  @override
  String tripDetailsTruckInfo(String truckNumber, String truckModel) {
    return 'ट्रक: $truckNumber ($truckModel)';
  }

  @override
  String tripDetailsDriverInfo(String driverName) {
    return 'ड्राइवर: $driverName';
  }

  @override
  String tripDetailsClientLabel(String name) {
    return 'ग्राहक: $name';
  }

  @override
  String get tripDetailsTabOverview => 'अवलोकन';

  @override
  String get tripDetailsTabTimeline => 'टाइमलाइन';

  @override
  String get tripDetailsTabNotes => 'नोट्स';

  @override
  String get tripDetailsPickupLocation => 'पिकअप स्थान';

  @override
  String get tripDetailsDeliveryLocation => 'डिलीवरी स्थान';

  @override
  String get tripDetailsDistance => 'दूरी';

  @override
  String get tripDetailsLoadWeight => 'लोड वज़न';

  @override
  String get tripDetailsDeparture => 'प्रस्थान';

  @override
  String get tripDetailsViewRoute => 'रूट देखें';

  @override
  String get tripDetailsMapPreviewNote =>
      'मैप पूर्वावलोकन उदाहरण के लिए है — लाइव रूट के लिए सक्रिय ट्रिप (मैप दृश्य) देखें।';

  @override
  String get tripDetailsNoDocuments =>
      'इस ट्रिप के लिए अभी कोई दस्तावेज़ नहीं है।';

  @override
  String get tripDetailsSpecialInstructions => 'विशेष निर्देश';

  @override
  String get tripDetailsHazardousNote =>
      'सावधानी से संभालें — खतरनाक सामग्री। लोडिंग/अनलोडिंग के दौरान ड्राइवर को PPE पहनना अनिवार्य है।';

  @override
  String get tripDetailsStartTrip => 'ट्रिप शुरू करें';

  @override
  String get tripDetailsMarkDelivered => 'डिलीवर के रूप में चिह्नित करें';

  @override
  String get tripDetailsCheckpointLoaded => 'लोड हो गया';

  @override
  String get tripDetailsCheckpointReachedDestination => 'गंतव्य पर पहुंचे';

  @override
  String get tripDetailsCheckpointRecorded => 'चेकपॉइंट दर्ज किया गया';

  @override
  String get timelineTripCreated => 'ट्रिप बनाई गई';

  @override
  String get timelineConfirmedByDispatcher => 'डिस्पैचर द्वारा पुष्टि की गई';

  @override
  String get timelineTruckAndDriverAllocated => 'ट्रक और ड्राइवर असाइन किए गए';

  @override
  String get timelineTripStarted => 'ट्रिप शुरू हुई';

  @override
  String get timelineDelivered => 'डिलीवर किया गया';

  @override
  String get timelinePending => 'लंबित';

  @override
  String get activeTripTitle => 'सक्रिय ट्रिप';

  @override
  String get activeTripRefreshTooltip => 'स्थान और ईटीए रीफ़्रेश करें';

  @override
  String get activeTripNextStep => 'अगला कदम';

  @override
  String get activeTripReachPickupLocation => 'पिकअप स्थान पर पहुंचें';

  @override
  String get activeTripReachedPickup => 'पिकअप पर पहुंचे';

  @override
  String get activeTripSharingLocation => 'लाइव स्थान साझा किया जा रहा है';

  @override
  String get podTitle => 'डिलीवरी का प्रमाण';

  @override
  String get podDeliveryPhoto => 'डिलीवरी फ़ोटो';

  @override
  String get podPhotoUploaded => '1 फ़ोटो अपलोड की गई';

  @override
  String get podNoPhotoYet => 'अभी कोई फ़ोटो नहीं';

  @override
  String get podRetake => 'फिर से लें';

  @override
  String get podReceiverSignature => 'प्राप्तकर्ता हस्ताक्षर';

  @override
  String get podTapToSign => 'हस्ताक्षर करने के लिए टैप करें';

  @override
  String get podClear => 'साफ़ करें';

  @override
  String get podReceiverName => 'प्राप्तकर्ता का नाम';

  @override
  String get podReceiverNameHint => 'प्राप्तकर्ता का नाम दर्ज करें';

  @override
  String get podRemarksOptional => 'टिप्पणी (वैकल्पिक)';

  @override
  String get podRemarksHint => 'डिलीवरी के बारे में कोई टिप्पणी जोड़ें';

  @override
  String get podSubmit => 'डिलीवरी का प्रमाण सबमिट करें';

  @override
  String get podSubmittedDemo =>
      'डिलीवरी का प्रमाण सबमिट किया गया (केवल डेमो)।';

  @override
  String get profileTitle => 'प्रोफ़ाइल';

  @override
  String get profileVerified => 'सत्यापित';

  @override
  String get profilePhone => 'फ़ोन';

  @override
  String get profileEmail => 'ईमेल';

  @override
  String get profileLicenseNo => 'लाइसेंस नंबर';

  @override
  String get profileEmergencyContact => 'आपातकालीन संपर्क';

  @override
  String get profileAddress => 'पता';

  @override
  String get profileVehicleInformation => 'वाहन की जानकारी';

  @override
  String get profileDocuments => 'दस्तावेज़';

  @override
  String get profileSettings => 'सेटिंग्स';

  @override
  String get profileDarkMode => 'डार्क मोड';

  @override
  String get profileLanguage => 'भाषा';

  @override
  String get profileLogOut => 'लॉग आउट';

  @override
  String get profileAvatarUpdated => 'प्रोफ़ाइल फ़ोटो अपडेट की गई।';

  @override
  String get profileAvatarUpdateFailed =>
      'प्रोफ़ाइल फ़ोटो अपडेट करने में विफल।';

  @override
  String get navShipments => 'शिपमेंट';

  @override
  String get navInvoices => 'इनवॉइस';

  @override
  String get clientShipmentsTitle => 'मेरे शिपमेंट';

  @override
  String get clientShipmentsEmpty => 'कोई शिपमेंट नहीं मिला';

  @override
  String get clientNewShipment => 'नया शिपमेंट';

  @override
  String get loadStatusAll => 'सभी';

  @override
  String get loadStatusDraft => 'ड्राफ्ट';

  @override
  String get loadStatusConfirmed => 'पुष्टि की गई';

  @override
  String get loadStatusAllocated => 'आवंटित';

  @override
  String get loadStatusInTransit => 'ट्रांज़िट में';

  @override
  String get loadStatusDelivered => 'डिलीवर हो गया';

  @override
  String get loadStatusCancelled => 'रद्द';

  @override
  String get bookingCarrier => 'कैरियर';

  @override
  String get bookingOrigin => 'मूल स्थान';

  @override
  String get bookingDestination => 'गंतव्य';

  @override
  String get bookingPickupDate => 'पिकअप तिथि';

  @override
  String get bookingGoodsType => 'माल का प्रकार';

  @override
  String get bookingGoodsDescription => 'माल का विवरण (वैकल्पिक)';

  @override
  String get bookingWeightKg => 'वज़न (किग्रा)';

  @override
  String get bookingQuantity => 'मात्रा';

  @override
  String get bookingTruckPreference => 'ट्रक प्राथमिकता (वैकल्पिक)';

  @override
  String get bookingSpecialInstructions => 'विशेष निर्देश (वैकल्पिक)';

  @override
  String get bookingNotes => 'टिप्पणी (वैकल्पिक)';

  @override
  String get bookingSubmit => 'बुकिंग अनुरोध सबमिट करें';

  @override
  String get bookingSubmitted => 'बुकिंग अनुरोध सबमिट हो गया';

  @override
  String get bookingFieldRequired => 'आवश्यक';

  @override
  String get bookingNoCarriers =>
      'आपकी प्रोफ़ाइल से अभी तक कोई कैरियर खाता लिंक नहीं है।';

  @override
  String get clientShipmentDetailsTitle => 'शिपमेंट विवरण';

  @override
  String get shipmentGoodsType => 'माल का प्रकार';

  @override
  String get shipmentWeight => 'वज़न';

  @override
  String get shipmentVolume => 'आयतन';

  @override
  String get shipmentQuantity => 'मात्रा';

  @override
  String get shipmentFreightAmount => 'भाड़ा राशि';

  @override
  String get shipmentAdvanceAmount => 'अग्रिम राशि';

  @override
  String get shipmentBalanceAmount => 'शेष राशि';

  @override
  String get shipmentExpectedDelivery => 'अनुमानित डिलीवरी';

  @override
  String get shipmentActualDelivery => 'वास्तविक डिलीवरी';

  @override
  String get shipmentTruckPreference => 'ट्रक प्राथमिकता';

  @override
  String get shipmentNoHistory => 'अभी तक कोई स्थिति इतिहास नहीं है।';

  @override
  String get shipmentNoDocuments =>
      'इस शिपमेंट के लिए अभी तक कोई दस्तावेज़ नहीं है।';

  @override
  String get notesLabel => 'टिप्पणी';

  @override
  String get clientInvoicesTitle => 'मेरे इनवॉइस';

  @override
  String get clientInvoicesEmpty => 'कोई इनवॉइस नहीं मिला';

  @override
  String get invoiceStatusAll => 'सभी';

  @override
  String get invoiceStatusSent => 'भेजा गया';

  @override
  String get invoiceStatusPartial => 'आंशिक रूप से भुगतान';

  @override
  String get invoiceStatusPaid => 'भुगतान हो गया';

  @override
  String get invoiceStatusOverdue => 'अतिदेय';

  @override
  String get invoiceSubtotal => 'उप-योग';

  @override
  String get invoiceTax => 'कर';

  @override
  String get invoiceTotal => 'कुल राशि';

  @override
  String get invoicePaid => 'भुगतान की गई राशि';

  @override
  String get invoiceOutstanding => 'बकाया राशि';

  @override
  String get invoiceIssuedDate => 'जारी करने की तिथि';

  @override
  String get invoiceDueDate => 'देय तिथि';

  @override
  String get invoiceDownloadPdf => 'PDF डाउनलोड करें';

  @override
  String get invoiceDownloaded => 'इनवॉइस डाउनलोड हो गया';

  @override
  String get invoiceDownloadFailed => 'इनवॉइस डाउनलोड करने में विफल';

  @override
  String get invoicePaymentHistory => 'भुगतान इतिहास';

  @override
  String get invoiceNoPayments => 'अभी तक कोई भुगतान दर्ज नहीं किया गया है।';

  @override
  String invoicePaymentReference(String reference) {
    return 'संदर्भ: $reference';
  }

  @override
  String get clientProfileTitle => 'मेरी प्रोफ़ाइल';

  @override
  String get clientCompanyName => 'कंपनी का नाम';

  @override
  String get clientNoCarriers => 'कोई कैरियर संबंध नहीं मिला।';

  @override
  String get clientContactPerson => 'संपर्क व्यक्ति';

  @override
  String get clientDashboardGreeting => 'वापसी पर स्वागत है,';

  @override
  String get clientShipmentSummary => 'शिपमेंट सारांश';

  @override
  String get clientRecentShipments => 'हाल के शिपमेंट';

  @override
  String get clientTotalOutstanding => 'कुल बकाया';

  @override
  String get shipmentOpenInMaps => 'मैप्स में खोलें';

  @override
  String get clientNotLinked =>
      'आपका खाता अभी किसी कस्टमर पोर्टल से लिंक नहीं है। कृपया अपने कैरियर से संपर्क करें।';

  @override
  String get clientGenericError =>
      'कुछ गलत हो गया। पुनः प्रयास करने के लिए रिफ्रेश करें।';

  @override
  String get clientAllCarriers => 'सभी';

  @override
  String get clientEditShipment => 'शिपमेंट संपादित करें';

  @override
  String get clientSaveChanges => 'बदलाव सहेजें';

  @override
  String get clientCancelShipment => 'शिपमेंट रद्द करें';

  @override
  String get clientCancelConfirmMessage =>
      'क्या आप वाकई इस शिपमेंट अनुरोध को रद्द करना चाहते हैं?';

  @override
  String get clientCancelReason => 'रद्द करने का कारण';

  @override
  String get clientCancelReasonHint => 'कृपया कम से कम 5 अक्षर दर्ज करें';

  @override
  String get clientShipmentCancelled => 'शिपमेंट रद्द कर दिया गया';

  @override
  String get clientShipmentUpdated => 'शिपमेंट अपडेट हो गया';

  @override
  String get clientUpdateFailed => 'शिपमेंट अपडेट करने में विफल';

  @override
  String get clientUploadDocument => 'दस्तावेज़ अपलोड करें';

  @override
  String get clientDocumentUploaded => 'दस्तावेज़ अपलोड हो गया';

  @override
  String get clientDocumentUploadFailed => 'दस्तावेज़ अपलोड करने में विफल';
}
