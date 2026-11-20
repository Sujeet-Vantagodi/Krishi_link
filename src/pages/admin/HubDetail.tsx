import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { API_DEMO_MODE, requestApi } from '../../lib/api/client';
import { useParams, useNavigate } from 'react-router-dom';
import { useHubDetail, useStockMatrix } from '../../features/hubs/hooks';
import { useAdminTrips } from '../../features/trips/hooks';
import { StockStatusButtons } from '../../components/stock/StockStatusButtons';
import { LiveMap } from '../../components/map/LiveMap';
import { Button } from '../../components/ui/button';
import { ArrowLeft, Warehouse, Users, Truck, History } from 'lucide-react';
import { TableSkeleton } from '../../components/common/Skeletons';

export const HubDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: hub, isLoading: hubLoading } = useHubDetail(id || '');
  const { data: matrixData } = useStockMatrix();
  const { data: trips = [] } = useAdminTrips(API_DEMO_MODE);
  const queries = useQueryClient();
  const [tripId, setTripId] = useState('');
  const [cropId, setCropId] = useState('');
  const inbound = useQuery({
    queryKey: ['hub-inbound', id],
    enabled: !!id && !API_DEMO_MODE,
    queryFn: () => requestApi<{ items: { id: string; type: string; status: string; crops: Record<string, string> }[] }>(`/hubs/${id}/inbound-trips`),
  });
  const weighIn = useMutation({
    mutationFn: (weights: Record<string, number>) => requestApi(
      `/admin/trips/${tripId}/hub-receive?hub_id=${id}`, 'POST', { crop_id: cropId, ...weights },
    ),
    onSuccess: () => {
      setCropId('');
      void queries.invalidateQueries({ queryKey: ['hub-inbound', id] });
      void queries.invalidateQueries({ queryKey: ['stock_matrix'] });
    },
  });

  if (hubLoading || !hub) {
    return <TableSkeleton rows={4} />;
  }

  const tripCount = API_DEMO_MODE ? trips.filter((trip) => trip.hub_id === hub.id).length : inbound.data?.items.length;

  return (
    <div className="space-y-6">
      <div>
        <button
          onClick={() => navigate('/admin/hubs')}
          className="flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-900 mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Hubs</span>
        </button>
        <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
          {hub.name}
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">{hub.address}</p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-bold uppercase">Classification</span>
          <p className="text-base font-black text-slate-900 dark:text-white mt-1 capitalize">
            {hub.type} hub
          </p>
        </div>
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-bold uppercase">Capacity</span>
          <p className="text-base font-black text-slate-900 dark:text-white mt-1">
            {hub.capacity_kg.toLocaleString()} kg
          </p>
        </div>
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-bold uppercase">Cold Storage</span>
          <p className="text-base font-black text-emerald-600 mt-1">
            {hub.has_cold_room ? 'Available ✓' : 'Ambient Only'}
          </p>
        </div>
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-bold uppercase">Scheduled Trips</span>
          <p className="text-base font-black text-blue-600 mt-1">{tripCount == null ? 'Unavailable' : `${tripCount} Trips`}</p>
        </div>
      </div>

      {/* Hub Map */}
      <div className="rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm bg-white">
        <LiveMap center={hub.location} zoom={12} hubs={[hub]} className="h-64 w-full" />
      </div>

      {/* Stock Status for this hub */}
      {!API_DEMO_MODE && (
        <form className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4" onSubmit={(event) => {
          event.preventDefault();
          const fields = new FormData(event.currentTarget);
          weighIn.mutate(Object.fromEntries(['kg_hub', 'grade_a_kg', 'grade_b_kg', 'reject_kg'].map((key) => [key, Number(fields.get(key))])));
        }}>
          <h3 className="text-base font-black text-slate-900 dark:text-white">Inbound Pickup Receipt</h3>
          <label className="block text-xs font-bold text-slate-500">Inbound trip
            <select className="w-full rounded-xl border border-slate-200 p-2.5 dark:bg-slate-800" value={tripId} onChange={(event) => { setTripId(event.target.value); setCropId(''); weighIn.reset(); }} required>
              <option value="">Select an arrived pickup trip</option>
              {inbound.data?.items.filter((trip) => trip.type === 'FIRST_MILE' && trip.status === 'AT_HUB' && Object.keys(trip.crops).length).map((trip) => (
                <option key={trip.id} value={trip.id}>{trip.id}</option>
              ))}
            </select>
          </label>
          <label className="block text-xs font-bold text-slate-500">Crop
            <select className="w-full rounded-xl border border-slate-200 p-2.5 dark:bg-slate-800" value={cropId} onChange={(event) => setCropId(event.target.value)} required>
              <option value="">Select crop</option>
              {Object.entries(inbound.data?.items.find((trip) => trip.id === tripId)?.crops ?? {}).map(([key, name]) => <option key={key} value={key}>{name}</option>)}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries({ kg_hub: 'Measured total (kg)', grade_a_kg: 'Grade A (kg)', grade_b_kg: 'Grade B (kg)', reject_kg: 'Rejected (kg)' }).map(([key, label]) => (
              <label key={key} className="text-xs font-bold text-slate-500">{label}
                <input name={key} type="number" min={key === 'kg_hub' ? '0.001' : '0'} step="0.001" required className="w-full rounded-xl border border-slate-200 p-2.5 dark:bg-slate-800" />
              </label>
            ))}
          </div>
          {(inbound.error || weighIn.error) && <p role="alert" className="text-xs text-red-600">{(inbound.error || weighIn.error)?.message}</p>}
          {weighIn.isSuccess && <p role="status" className="text-xs text-emerald-600">Hub receipt recorded.</p>}
          <Button type="submit" disabled={!tripId || !cropId || weighIn.isPending}>Record Hub Receipt</Button>
        </form>
      )}
      {matrixData && (
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
          <h3 className="text-base font-black text-slate-900 dark:text-white">
            Current Produce Inventory Status
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {matrixData.crops.map((crop) => {
              const cell = matrixData.matrix[hub.id]?.[crop.id] || { status: 'SUFFICIENT' };
              return (
                <div
                  key={crop.id}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{crop.image_emoji}</span>
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                      {crop.name_en}
                    </span>
                  </div>
                  <StockStatusButtons
                    value={cell.status}
                    size="sm"
                    onChange={() => {}}
                    disabled={true}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
