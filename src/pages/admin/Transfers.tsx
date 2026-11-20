import React, { useState } from 'react';
import { useTransfers, useUpdateTransferStatus } from '../../features/transfers/hooks';
import { TransferRequestCard } from '../../components/admin/TransferRequestCard';
import { TransferStatus } from '../../types';
import { ArrowLeftRight, Check, Plus } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Dialog, DialogTitle } from '../../components/ui/dialog';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { API_DEMO_MODE, requestApi } from '../../lib/api/client';
import { getAvailableDrivers } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';

export const Transfers: React.FC = () => {
  const { data: transfers = [] } = useTransfers();
  const updateStatusMutation = useUpdateTransferStatus();
  const queries = useQueryClient();
  const role = useAuthStore((state) => state.role);
  const canDispatch = API_DEMO_MODE || role === 'admin';
  const [action, setAction] = useState<{ id: string; kind: 'assign' | 'dispatch' | 'receive'; trip?: string }>();
  const [input, setInput] = useState('');
  const choices = useQuery({
    queryKey: ['transfer-trips', action?.id],
    enabled: action?.kind === 'assign',
    queryFn: () => requestApi<{ items: { id: string; driver: string; vehicle: string }[] }>(`/transfers/${action!.id}/eligible-trips`),
  });
  const drivers = useQuery({
    queryKey: ['available_drivers'],
    enabled: action?.kind === 'assign',
    queryFn: getAvailableDrivers,
  });
  const recordAction = useMutation({
    mutationFn: async (current: NonNullable<typeof action>) => {
      let assignedTrip = input;
      if (current.kind === 'assign' && input.startsWith('driver:')) {
        const driver = drivers.data?.find(({ user_id }) => user_id === input.slice(7));
        const transfer = transfers.find(({ id }) => id === current.id);
        if (!driver?.vehicle || !transfer) throw new Error('Select an available driver with a vehicle');
        const trip = await requestApi<{ id: string }>('/admin/assign', 'POST', {
          type: 'TRANSFER', driver_user_id: driver.user_id, vehicle_id: driver.vehicle.id,
          origin_hub_id: transfer.from_hub_id, dest_hub_id: transfer.to_hub_id, stops: [],
        });
        assignedTrip = trip.id;
        setInput(trip.id);
        void queries.invalidateQueries({ queryKey: ['transfer-trips', current.id] });
      }
      return requestApi(
      `/transfers/${current.id}/${current.kind}`, 'POST',
      current.kind === 'assign' ? { trip_id: assignedTrip }
        : current.kind === 'dispatch' ? { trip_id: current.trip, sent_kg: Number(input) }
        : { received_kg: Number(input) },
      );
    },
    onSuccess: () => {
      setAction(undefined);
      void queries.invalidateQueries({ queryKey: ['transfers'] });
      void queries.invalidateQueries({ queryKey: ['stock_matrix'] });
    },
  });

  const openAction = (next: NonNullable<typeof action>) => {
    setInput('');
    recordAction.reset();
    setAction(next);
  };

  const columns: { id: TransferStatus; label: string; color: string }[] = [
    { id: 'REQUESTED', label: 'Requested', color: 'border-t-amber-500' },
    { id: 'APPROVED', label: 'Approved', color: 'border-t-blue-500' },
    { id: 'ASSIGNED', label: 'Assigned Driver', color: 'border-t-indigo-500' },
    { id: 'IN_TRANSIT', label: 'In Transit 🚚', color: 'border-t-purple-500' },
    { id: 'RECEIVED', label: 'Received at Hub ✓', color: 'border-t-emerald-500' },
  ];

  const handleApprove = (id: string) => {
    updateStatusMutation.mutate({ id, status: 'APPROVED' });
  };

  const handleAssignDriver = (id: string) => {
    if (API_DEMO_MODE) return updateStatusMutation.mutate({ id, status: 'IN_TRANSIT' });
    const transfer = transfers.find((row) => row.id === id);
    openAction({ id, kind: transfer?.status === 'ASSIGNED' ? 'dispatch' : 'assign', trip: transfer?.trip_id });
  };

  const handleReject = (id: string) => {
    updateStatusMutation.mutate({ id, status: 'REJECTED' });
  };

  const handleReceive = (id: string) => {
    if (API_DEMO_MODE) return updateStatusMutation.mutate({ id, status: 'RECEIVED' });
    openAction({ id, kind: 'receive' });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Inter-Hub Stock Transfers
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Lateral produce rebalancing across village and city hubs to avert shortages.
          </p>
        </div>
      </div>

      {/* Kanban Board Columns */}
      {updateStatusMutation.error && <p role="alert" className="text-sm text-red-600">{updateStatusMutation.error.message}</p>}
      <Dialog open={!!action} onOpenChange={(open) => { if (!open && !recordAction.isPending) setAction(undefined); }}>
        <DialogTitle>{action?.kind === 'assign' ? 'Assign Transfer Trip' : action?.kind === 'dispatch' ? 'Dispatch Transfer' : 'Confirm Received at Hub'}</DialogTitle>
        <form className="space-y-3 mt-4" onSubmit={(event) => { event.preventDefault(); if (action) recordAction.mutate(action); }}>
          <label className="block text-xs font-bold text-slate-500">
            {action?.kind === 'assign' ? 'Transfer trip' : action?.kind === 'dispatch' ? 'Measured sent weight (kg)' : 'Measured received weight (kg)'}
            {action?.kind === 'assign'
              ? <select required className="w-full rounded-xl border border-slate-200 p-2.5 dark:bg-slate-800" value={input} onChange={(event) => setInput(event.target.value)}>
                  <option value="">Select an assigned trip</option>
                  {choices.data?.items.map((row) => <option key={row.id} value={row.id}>{row.driver} · {row.vehicle} · {row.id.slice(0, 8)}</option>)}
                  {drivers.data?.filter((driver) => driver.vehicle).map((driver) => (
                    <option key={driver.user_id} value={`driver:${driver.user_id}`}>New trip · {driver.name} · {driver.vehicle?.reg_no}</option>
                  ))}
                </select>
              : <input required type="number" min="0.01" step="0.01" className="w-full rounded-xl border border-slate-200 p-2.5 dark:bg-slate-800" value={input} onChange={(event) => setInput(event.target.value)} />}
          </label>
          {choices.error && action?.kind === 'assign' && <p role="alert" className="text-xs text-red-600">{choices.error.message}</p>}
          {action?.kind === 'assign' && drivers.error && <p role="alert" className="text-xs text-red-600">{drivers.error.message}</p>}
          {recordAction.error && <p role="alert" className="text-xs text-red-600">{recordAction.error.message}</p>}
          <Button type="submit" disabled={!input || recordAction.isPending}>Confirm</Button>
        </form>
      </Dialog>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 overflow-x-auto pb-4">
        {columns.map((col) => {
          const colItems = transfers.filter((t) => t.status === col.id);

          return (
            <div
              key={col.id}
              className={`rounded-2xl bg-slate-100/70 dark:bg-slate-800/50 p-3 border border-slate-200 dark:border-slate-800 border-t-4 ${col.color} flex flex-col min-h-[480px]`}
            >
              <div className="flex items-center justify-between mb-3 px-1">
                <h4 className="text-xs font-black uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  {col.label}
                </h4>
                <span className="h-5 w-5 rounded-full bg-slate-200 dark:bg-slate-700 text-xs font-bold flex items-center justify-center text-slate-700 dark:text-slate-200">
                  {colItems.length}
                </span>
              </div>

              <div className="space-y-3 flex-1 overflow-y-auto">
                {colItems.length === 0 ? (
                  <div className="h-28 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-700 flex items-center justify-center text-[11px] text-slate-400 font-medium">
                    No requests
                  </div>
                ) : (
                  colItems.map((tr) => (
                    <TransferRequestCard
                      key={tr.id}
                      transfer={tr}
                      onApprove={canDispatch ? handleApprove : undefined}
                      onAssignDriver={canDispatch ? handleAssignDriver : undefined}
                      onReject={canDispatch ? handleReject : undefined}
                      onReceive={handleReceive}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
