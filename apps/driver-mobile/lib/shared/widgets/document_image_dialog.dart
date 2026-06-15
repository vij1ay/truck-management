import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Full-screen view of a single document's image bytes, fetched via
/// [provider] (e.g. `shipmentDocumentBytesProvider((loadId, documentId))` or
/// `tripDocumentBytesProvider((tripId, documentId))`). Shared by the Client
/// Portal's and the driver app's Documents tabs.
class DocumentImageDialog extends ConsumerWidget {
  const DocumentImageDialog({super.key, required this.provider});

  final ProviderListenable<AsyncValue<List<int>>> provider;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bytesAsync = ref.watch(provider);

    return Dialog(
      insetPadding: const EdgeInsets.all(16),
      child: Stack(
        alignment: Alignment.topRight,
        children: [
          ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 200, minWidth: 200),
            child: bytesAsync.when(
              data: (bytes) => InteractiveViewer(
                child: Image.memory(Uint8List.fromList(bytes)),
              ),
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (_, __) => const Center(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: Icon(Icons.broken_image_outlined, size: 48),
                ),
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }
}
