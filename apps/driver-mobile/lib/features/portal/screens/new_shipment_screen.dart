import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/providers/portal_provider.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/models/shipment.dart';
import '../../../shared/widgets/primary_button.dart';
import '../../../shared/utils/goods_type.dart';
import '../utils/portal_error.dart';

/// "New Shipment" / "Edit Shipment" — a booking request submitted to one of
/// the shipper's linked carriers (`POST /portal/loads`), mirroring the
/// admin-frontend's booking form (`shipment-list.component.ts`). When
/// [editing] is set, the form is pre-filled and submits via
/// `PATCH /portal/loads/{id}` instead (the carrier can't be changed).
class NewShipmentScreen extends ConsumerStatefulWidget {
  const NewShipmentScreen({super.key, this.editing});

  final Shipment? editing;

  @override
  ConsumerState<NewShipmentScreen> createState() => _NewShipmentScreenState();
}

class _NewShipmentScreenState extends ConsumerState<NewShipmentScreen> {
  final _formKey = GlobalKey<FormState>();

  final _originController = TextEditingController();
  final _destinationController = TextEditingController();
  final _goodsDescriptionController = TextEditingController();
  final _weightController = TextEditingController();
  final _quantityController = TextEditingController();
  final _truckPreferenceController = TextEditingController();
  final _specialInstructionsController = TextEditingController();
  final _notesController = TextEditingController();

  String? _tenantId;
  DateTime? _pickupDate;
  String _goodsType = goodsTypes.first;
  bool _submitting = false;
  bool _autoSelectedCarrier = false;

  @override
  void initState() {
    super.initState();
    final editing = widget.editing;
    if (editing != null) {
      _originController.text = editing.origin;
      _destinationController.text = editing.destination;
      _goodsDescriptionController.text = editing.goodsDescription ?? '';
      _weightController.text = editing.weightKg?.toString() ?? '';
      _quantityController.text = editing.quantity?.toString() ?? '';
      _truckPreferenceController.text = editing.truckPreference ?? '';
      _specialInstructionsController.text = editing.specialInstructions ?? '';
      _notesController.text = editing.notes ?? '';
      _goodsType = editing.goodsType;
      _pickupDate = DateTime.tryParse(editing.pickupDate);
      _tenantId = editing.tenantId;
      _autoSelectedCarrier = true; // don't auto-select/overwrite in edit mode
    }
  }

  @override
  void dispose() {
    _originController.dispose();
    _destinationController.dispose();
    _goodsDescriptionController.dispose();
    _weightController.dispose();
    _quantityController.dispose();
    _truckPreferenceController.dispose();
    _specialInstructionsController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _pickupDate ?? now,
      firstDate: now.subtract(const Duration(days: 1)),
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked != null) setState(() => _pickupDate = picked);
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final editing = widget.editing;
    if (!_formKey.currentState!.validate() || _tenantId == null || _pickupDate == null) {
      setState(() {}); // re-validate to surface the date/carrier errors below
      return;
    }

    final payload = {
      'origin': _originController.text.trim(),
      'destination': _destinationController.text.trim(),
      'pickup_date': DateFormat('yyyy-MM-dd').format(_pickupDate!),
      'goods_type': _goodsType,
      if (_goodsDescriptionController.text.trim().isNotEmpty)
        'goods_description': _goodsDescriptionController.text.trim(),
      if (_weightController.text.trim().isNotEmpty)
        'weight_kg': double.tryParse(_weightController.text.trim()),
      if (_quantityController.text.trim().isNotEmpty)
        'quantity': int.tryParse(_quantityController.text.trim()),
      if (_truckPreferenceController.text.trim().isNotEmpty)
        'truck_preference': _truckPreferenceController.text.trim(),
      if (_specialInstructionsController.text.trim().isNotEmpty)
        'special_instructions': _specialInstructionsController.text.trim(),
      if (_notesController.text.trim().isNotEmpty) 'notes': _notesController.text.trim(),
    };

    setState(() => _submitting = true);
    try {
      if (editing == null) {
        await ref.read(portalRepositoryProvider).createShipment({
          'tenant_id': _tenantId,
          ...payload,
        });
        ref.invalidate(shipmentsProvider);
      } else {
        await ref.read(portalRepositoryProvider).updateShipment(editing.id, payload);
        ref.invalidate(shipmentsProvider);
        ref.invalidate(shipmentDetailProvider(editing.id));
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(editing == null ? l10n.bookingSubmitted : l10n.clientShipmentUpdated)),
        );
        Navigator.of(context).pop();
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(editing == null ? 'Failed to submit booking request.' : l10n.clientUpdateFailed)),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final carriersAsync = ref.watch(myCarriersProvider);

    final isEditing = widget.editing != null;

    return Scaffold(
      appBar: AppBar(title: Text(isEditing ? l10n.clientEditShipment : l10n.clientNewShipment)),
      body: carriersAsync.when(
        data: (carriers) {
          if (carriers.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(l10n.bookingNoCarriers, textAlign: TextAlign.center),
              ),
            );
          }
          if (!_autoSelectedCarrier) {
            _autoSelectedCarrier = true;
            if (carriers.length == 1) _tenantId = carriers.first.tenantId;
          }

          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (isEditing)
                  InputDecorator(
                    decoration: InputDecoration(labelText: l10n.bookingCarrier),
                    child: Text(
                      carriers
                          .firstWhere(
                            (c) => c.tenantId == _tenantId,
                            orElse: () => carriers.first,
                          )
                          .tenantName,
                    ),
                  )
                else
                  DropdownButtonFormField<String>(
                    value: _tenantId,
                    decoration: InputDecoration(labelText: l10n.bookingCarrier),
                    items: [
                      for (final carrier in carriers)
                        DropdownMenuItem(
                          value: carrier.tenantId,
                          child: Text(carrier.tenantName),
                        ),
                    ],
                    onChanged: (value) => setState(() => _tenantId = value),
                    validator: (value) => value == null ? l10n.bookingFieldRequired : null,
                  ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _originController,
                  decoration: InputDecoration(labelText: l10n.bookingOrigin),
                  validator: (value) =>
                      (value == null || value.trim().isEmpty) ? l10n.bookingFieldRequired : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _destinationController,
                  decoration: InputDecoration(labelText: l10n.bookingDestination),
                  validator: (value) =>
                      (value == null || value.trim().isEmpty) ? l10n.bookingFieldRequired : null,
                ),
                const SizedBox(height: 16),
                InkWell(
                  onTap: _pickDate,
                  child: InputDecorator(
                    decoration: InputDecoration(
                      labelText: l10n.bookingPickupDate,
                      suffixIcon: const Icon(Icons.calendar_today_outlined),
                    ),
                    child: Text(
                      _pickupDate == null
                          ? ''
                          : DateFormat('yyyy-MM-dd').format(_pickupDate!),
                    ),
                  ),
                ),
                if (_pickupDate == null)
                  Padding(
                    padding: const EdgeInsets.only(top: 6, left: 12),
                    child: Text(
                      l10n.bookingFieldRequired,
                      style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12),
                    ),
                  ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: _goodsType,
                  decoration: InputDecoration(labelText: l10n.bookingGoodsType),
                  items: [
                    for (final type in goodsTypes)
                      DropdownMenuItem(value: type, child: Text(goodsTypeLabel(type))),
                  ],
                  onChanged: (value) => setState(() => _goodsType = value ?? _goodsType),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _goodsDescriptionController,
                  decoration: InputDecoration(labelText: l10n.bookingGoodsDescription),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _weightController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(labelText: l10n.bookingWeightKg),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextFormField(
                        controller: _quantityController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(labelText: l10n.bookingQuantity),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _truckPreferenceController,
                  decoration: InputDecoration(labelText: l10n.bookingTruckPreference),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _specialInstructionsController,
                  maxLines: 2,
                  decoration: InputDecoration(labelText: l10n.bookingSpecialInstructions),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _notesController,
                  maxLines: 2,
                  decoration: InputDecoration(labelText: l10n.bookingNotes),
                ),
                const SizedBox(height: 24),
                PrimaryButton(
                  label: isEditing ? l10n.clientSaveChanges : l10n.bookingSubmit,
                  icon: isEditing ? Icons.save_outlined : Icons.send_outlined,
                  loading: _submitting,
                  onPressed: _submit,
                ),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(portalErrorMessage(l10n, err), textAlign: TextAlign.center),
          ),
        ),
      ),
    );
  }
}
