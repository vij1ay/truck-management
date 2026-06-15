import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:signature/signature.dart';

import '../../../core/providers/trip_provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/primary_button.dart';

/// Proof of Delivery — captures a delivery photo and (optional) signature,
/// both uploaded via `POST /loads/{id}/documents/pod`, then on submit records
/// a "Delivered to ..." checkpoint and transitions the trip to DELIVERED
/// (`POST /loads/{id}/deliver`).
class ProofOfDeliveryScreen extends ConsumerStatefulWidget {
  const ProofOfDeliveryScreen({super.key, required this.tripId});

  final String tripId;

  @override
  ConsumerState<ProofOfDeliveryScreen> createState() => _ProofOfDeliveryScreenState();
}

class _ProofOfDeliveryScreenState extends ConsumerState<ProofOfDeliveryScreen> {
  final _receiverController = TextEditingController();
  final _remarksController = TextEditingController();
  late final SignatureController _signatureController;
  XFile? _photo;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _signatureController = SignatureController(
      penStrokeWidth: 3,
      penColor: Colors.black,
      exportBackgroundColor: Colors.white,
    );
  }

  @override
  void dispose() {
    _receiverController.dispose();
    _remarksController.dispose();
    _signatureController.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto() async {
    final picked = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      maxWidth: 1600,
      imageQuality: 85,
    );
    if (picked != null) setState(() => _photo = picked);
  }

  String _checkpointLabel() {
    final receiver = _receiverController.text.trim();
    final remarks = _remarksController.text.trim();
    String label;
    if (receiver.isNotEmpty && remarks.isNotEmpty) {
      label = 'Delivered to $receiver: $remarks';
    } else if (receiver.isNotEmpty) {
      label = 'Delivered to $receiver';
    } else if (remarks.isNotEmpty) {
      label = 'Delivered: $remarks';
    } else {
      label = 'Delivered';
    }
    return label.length > 100 ? label.substring(0, 100) : label;
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    if (_photo == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.podNoPhotoYet)),
      );
      return;
    }

    setState(() => _submitting = true);
    final repo = ref.read(tripRepositoryProvider);
    try {
      await repo.uploadPodPhoto(widget.tripId, _photo!.path);

      if (_signatureController.isNotEmpty) {
        final bytes = await _signatureController.toPngBytes();
        if (bytes != null) {
          final dir = await getTemporaryDirectory();
          final file = File('${dir.path}/signature_${widget.tripId}.png');
          await file.writeAsBytes(bytes, flush: true);
          await repo.uploadPodPhoto(widget.tripId, file.path);
        }
      }

      await repo.addCheckpoint(widget.tripId, _checkpointLabel());
      await repo.deliverTrip(widget.tripId);

      ref.invalidate(tripDetailProvider(widget.tripId));
      ref.invalidate(tripHistoryProvider(widget.tripId));
      ref.invalidate(tripDocumentsProvider(widget.tripId));
      ref.invalidate(tripsProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.podSubmittedDemo)),
        );
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.clientUpdateFailed)),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.podTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(l10n.podDeliveryPhoto, style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          AppCard(
            padding: EdgeInsets.zero,
            child: AspectRatio(
              aspectRatio: 16 / 9,
              child: Stack(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: _photo != null
                        ? Image.file(File(_photo!.path), fit: BoxFit.cover, width: double.infinity, height: double.infinity)
                        : Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              color: theme.brightness == Brightness.dark
                                  ? AppColors.darkSurfaceAlt
                                  : AppColors.lightSurfaceAlt,
                            ),
                            child: Center(
                              child: Icon(
                                Icons.inventory_2_outlined,
                                size: 48,
                                color: theme.textTheme.bodySmall?.color,
                              ),
                            ),
                          ),
                  ),
                  Positioned(
                    right: 12,
                    bottom: 12,
                    child: CircleAvatar(
                      backgroundColor: AppColors.primary,
                      child: IconButton(
                        icon: const Icon(
                          Icons.camera_alt,
                          color: Colors.white,
                          size: 20,
                        ),
                        onPressed: _pickPhoto,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Text(
                  _photo != null ? l10n.podPhotoUploaded : l10n.podNoPhotoYet,
                  style: theme.textTheme.bodySmall,
                ),
              ),
              if (_photo != null)
                TextButton(
                  onPressed: _pickPhoto,
                  child: Text(l10n.podRetake),
                ),
            ],
          ),
          const SizedBox(height: 24),

          Text(l10n.podReceiverSignature, style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          AppCard(
            child: Column(
              children: [
                AspectRatio(
                  aspectRatio: 21 / 9,
                  child: Stack(
                    children: [
                      Signature(
                        controller: _signatureController,
                        backgroundColor: theme.brightness == Brightness.dark
                            ? AppColors.darkSurfaceAlt
                            : AppColors.lightSurfaceAlt,
                      ),
                      ListenableBuilder(
                        listenable: _signatureController,
                        builder: (context, _) => _signatureController.isEmpty
                            ? Center(
                                child: IgnorePointer(
                                  child: Text(
                                    l10n.podTapToSign,
                                    style: theme.textTheme.bodyMedium,
                                  ),
                                ),
                              )
                            : const SizedBox.shrink(),
                      ),
                    ],
                  ),
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: _signatureController.clear,
                    child: Text(l10n.podClear),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          Text(l10n.podReceiverName, style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          TextField(
            controller: _receiverController,
            decoration: InputDecoration(hintText: l10n.podReceiverNameHint),
          ),
          const SizedBox(height: 24),

          Text(l10n.podRemarksOptional, style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          TextField(
            controller: _remarksController,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: l10n.podRemarksHint,
            ),
          ),
          const SizedBox(height: 32),

          PrimaryButton(
            label: l10n.podSubmit,
            icon: Icons.check_circle_outline,
            loading: _submitting,
            onPressed: _submit,
          ),
        ],
      ),
    );
  }
}
