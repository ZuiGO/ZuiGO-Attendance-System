import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Users,
  MapPin,
  Car,
  Clock,
  Search,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  DollarSign,
  Building2,
  Check,
  X,
  RefreshCw,
} from 'lucide-react';

interface EmployeePresence {
  id: string;
  name: string;
  code: string;
  department: string;
  office: string;
  clockInTime: string;
  currentTask: string | null;
  taskDurationSec: number;
  status: 'WORKING' | 'IDLE';
}

interface TravelClaim {
  id: string;
  employeeName: string;
  mode: string;
  date: string;
  odoDistanceKm: number;
  gpsDistanceKm: number;
  discrepancyPct: number;
  isFlagged: boolean;
  ratePerKm: number;
  totalAmount: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
}

const INITIAL_PRESENCE: EmployeePresence[] = [
  {
    id: 'emp-1',
    name: 'Alex Johnson',
    code: 'EMP-1001',
    department: 'Engineering',
    office: 'Headquarters (Floor 4)',
    clockInTime: '09:02 AM',
    currentTask: 'Implement On-Device Liveness Verification',
    taskDurationSec: 3240,
    status: 'WORKING',
  },
  {
    id: 'emp-2',
    name: 'Priya Sharma',
    code: 'EMP-1002',
    department: 'Sales & Field',
    office: 'Headquarters (Floor 4)',
    clockInTime: '08:55 AM',
    currentTask: 'North Hospital Beat Itinerary Prep',
    taskDurationSec: 4120,
    status: 'WORKING',
  },
  {
    id: 'emp-3',
    name: 'Rahul Verma',
    code: 'EMP-1003',
    department: 'Customer Success',
    office: 'Noida Branch',
    clockInTime: '09:14 AM',
    currentTask: null,
    taskDurationSec: 0,
    status: 'IDLE',
  },
  {
    id: 'emp-4',
    name: 'Sneha Patel',
    code: 'EMP-1004',
    department: 'Product',
    office: 'Headquarters (Floor 4)',
    clockInTime: '09:08 AM',
    currentTask: 'Field Verification Analytics Review',
    taskDurationSec: 1980,
    status: 'WORKING',
  },
];

const INITIAL_CLAIMS: TravelClaim[] = [
  {
    id: 'tc-1',
    employeeName: 'Priya Sharma',
    mode: 'PERSONAL_CAR',
    date: '2026-10-30',
    odoDistanceKm: 42.7,
    gpsDistanceKm: 41.3,
    discrepancyPct: 3.39,
    isFlagged: false,
    ratePerKm: 8.0,
    totalAmount: 330.4,
    status: 'PENDING',
  },
  {
    id: 'tc-2',
    employeeName: 'Vikram Singh',
    mode: 'PERSONAL_CAR',
    date: '2026-10-29',
    odoDistanceKm: 58.0,
    gpsDistanceKm: 38.2,
    discrepancyPct: 34.14,
    isFlagged: true, // Discrepancy > 15% fraud alert!
    ratePerKm: 8.0,
    totalAmount: 305.6,
    status: 'PENDING',
  },
  {
    id: 'tc-3',
    employeeName: 'Amit Joshi',
    mode: 'TWO_WHEELER',
    date: '2026-10-29',
    odoDistanceKm: 24.5,
    gpsDistanceKm: 23.8,
    discrepancyPct: 2.86,
    isFlagged: false,
    ratePerKm: 4.0,
    totalAmount: 95.2,
    status: 'APPROVED',
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'presence' | 'field' | 'reimbursements' | 'policy'>('presence');
  const [presenceList, setPresenceList] = useState<EmployeePresence[]>(INITIAL_PRESENCE);
  const [claimsList, setClaimsList] = useState<TravelClaim[]>(INITIAL_CLAIMS);
  const [searchQuery, setSearchQuery] = useState('');

  // Policy Settings State
  const [defaultDwellMins, setDefaultDwellMins] = useState(30);
  const [carRate, setCarRate] = useState(8.0);
  const [bikeRate, setBikeRate] = useState(4.0);
  const [discrepancyThreshold, setDiscrepancyThreshold] = useState(15.0);
  const [policySaved, setPolicySaved] = useState(false);

  // Live timer tick for active tasks
  useEffect(() => {
    const timer = setInterval(() => {
      setPresenceList(prev =>
        prev.map(item =>
          item.status === 'WORKING'
            ? { ...item, taskDurationSec: item.taskDurationSec + 1 }
            : item
        )
      );
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatSeconds = (sec: number) => {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    return `${h > 0 ? `${h}h ` : ''}${m}m ${s.toString().padStart(2, '0')}s`;
  };

  const handleClaimAction = (id: string, action: 'APPROVED' | 'REJECTED') => {
    setClaimsList(prev =>
      prev.map(claim => (claim.id === id ? { ...claim, status: action } : claim))
    );
  };

  const handleSavePolicy = () => {
    setPolicySaved(true);
    setTimeout(() => setPolicySaved(false), 2500);
  };

  const filteredPresence = presenceList.filter(
    p =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.currentTask && p.currentTask.toLowerCase().includes(searchQuery.toLowerCase())) ||
      p.department.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header Bar */}
      <header
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '16px 36px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
              padding: '10px 14px',
              borderRadius: '12px',
              fontWeight: 800,
              fontSize: '18px',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <ShieldCheck size={22} />
            ZuiGO Intelligence
          </div>
          <div>
            <h1 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>
              Employer Management Portal
            </h1>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Organization: ZuiGO Technologies</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '8px', background: '#0f172a', padding: '4px', borderRadius: '12px' }}>
          <button
            onClick={() => setActiveTab('presence')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'presence' ? '#2563eb' : 'transparent',
              color: activeTab === 'presence' ? '#ffffff' : '#94a3b8',
            }}
          >
            <Users size={16} /> Live Presence
          </button>
          <button
            onClick={() => setActiveTab('field')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'field' ? '#2563eb' : 'transparent',
              color: activeTab === 'field' ? '#ffffff' : '#94a3b8',
            }}
          >
            <MapPin size={16} /> Field Beats (50+ Locations)
          </button>
          <button
            onClick={() => setActiveTab('reimbursements')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'reimbursements' ? '#2563eb' : 'transparent',
              color: activeTab === 'reimbursements' ? '#ffffff' : '#94a3b8',
            }}
          >
            <Car size={16} /> Mileage & Claims
          </button>
          <button
            onClick={() => setActiveTab('policy')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
              background: activeTab === 'policy' ? '#2563eb' : 'transparent',
              color: activeTab === 'policy' ? '#ffffff' : '#94a3b8',
            }}
          >
            <Sliders size={16} /> Policies
          </button>
        </nav>
      </header>

      {/* Main Content Body */}
      <main style={{ padding: '32px 36px', flex: 1 }}>
        {/* TAB 1: LIVE PRESENCE BOARD */}
        {activeTab === 'presence' && (
          <div>
            {/* KPI Cards Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '28px' }}>
              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>Total Present Today</div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: '#4ade80', margin: '4px 0' }}>42</div>
                <div style={{ fontSize: '12px', color: '#86efac' }}>84.0% presence rate</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>Active Tasks Running</div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: '#60a5fa', margin: '4px 0' }}>36</div>
                <div style={{ fontSize: '12px', color: '#93c5fd' }}>Attendance-gated timers</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>Field Staff on Beat</div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: '#c084fc', margin: '4px 0' }}>14</div>
                <div style={{ fontSize: '12px', color: '#e9d5ff' }}>Hospital & dealer visits</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>Mileage Discrepancies</div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: '#f87171', margin: '4px 0' }}>1</div>
                <div style={{ fontSize: '12px', color: '#fca5a5' }}>⚠️ >15% Odometer gap flagged</div>
              </div>
            </div>

            {/* Filter and Search Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: '#0f172a', padding: '10px 16px', borderRadius: '12px', border: '1px solid #334155', width: '360px' }}>
                <Search size={18} color="#64748b" />
                <input
                  type="text"
                  placeholder="Search employee, task, department..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{ background: 'transparent', border: 'none', color: '#ffffff', outline: 'none', fontSize: '14px', width: '100%' }}
                />
              </div>

              <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                🟢 Real-time presence updates every second
              </div>
            </div>

            {/* Live Table */}
            <div style={{ background: '#0f172a', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                    <th style={{ padding: '16px 20px' }}>Employee</th>
                    <th style={{ padding: '16px 20px' }}>Department</th>
                    <th style={{ padding: '16px 20px' }}>Office Terminal</th>
                    <th style={{ padding: '16px 20px' }}>Clock In</th>
                    <th style={{ padding: '16px 20px' }}>Active Task</th>
                    <th style={{ padding: '16px 20px' }}>Tracked Time</th>
                    <th style={{ padding: '16px 20px' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPresence.map(row => (
                    <tr key={row.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontWeight: 700, color: '#f8fafc' }}>{row.name}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{row.code}</div>
                      </td>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{row.department}</td>
                      <td style={{ padding: '16px 20px', color: '#94a3b8' }}>{row.office}</td>
                      <td style={{ padding: '16px 20px', color: '#86efac', fontWeight: 600 }}>{row.clockInTime}</td>
                      <td style={{ padding: '16px 20px' }}>
                        {row.currentTask ? (
                          <span style={{ color: '#93c5fd', fontWeight: 600 }}>{row.currentTask}</span>
                        ) : (
                          <span style={{ color: '#64748b' }}>No active task</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#f8fafc' }}>
                        {row.status === 'WORKING' ? formatSeconds(row.taskDurationSec) : '—'}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '4px 10px',
                            borderRadius: '999px',
                            fontSize: '12px',
                            fontWeight: 700,
                            background: row.status === 'WORKING' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                            color: row.status === 'WORKING' ? '#4ade80' : '#fde047',
                          }}
                        >
                          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: row.status === 'WORKING' ? '#22c55e' : '#eab308' }} />
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: FIELD BEAT & ROUTE MONITORING */}
        {activeTab === 'field' && (
          <div>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                Field Beat Monitoring (50+ Locations)
              </h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                Real-time tracking of assigned hospital, distributor, and dealer visits. Enforces 30-min minimum dwell time & client SMS/WhatsApp OTP.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
              {/* Card 1: Apollo Hospital */}
              <div style={fieldCardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px' }}>STOP #1 • HOSPITAL</span>
                  <span style={{ background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80', fontSize: '11px', fontWeight: 700, padding: '3px 8px', borderRadius: '6px' }}>COMPLETED</span>
                </div>
                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>Apollo City Hospital</h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 12px 0' }}>Rep: Priya Sharma • Contact: Dr. Sharma</p>
                <div style={{ background: '#1e293b', borderRadius: '10px', padding: '10px', fontSize: '12px', color: '#cbd5e1', gap: '6px', display: 'flex', flexDirection: 'column' }}>
                  <div>⏱️ Dwell Time: <strong>32m 14s</strong> (Required: 30m) ✓</div>
                  <div>📱 Client Verification: <strong>SMS OTP #4921 Verified</strong> ✓</div>
                  <div>📷 Photo Proof: <strong>Watermark Hash #e9c12b Verified</strong> ✓</div>
                </div>
              </div>

              {/* Card 2: Metro Pharma */}
              <div style={fieldCardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px' }}>STOP #2 • DISTRIBUTOR</span>
                  <span style={{ background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80', fontSize: '11px', fontWeight: 700, padding: '3px 8px', borderRadius: '6px' }}>COMPLETED</span>
                </div>
                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>Metro Pharma Distributor</h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 12px 0' }}>Rep: Priya Sharma • Contact: Mr. Rajesh Gupta</p>
                <div style={{ background: '#1e293b', borderRadius: '10px', padding: '10px', fontSize: '12px', color: '#cbd5e1', gap: '6px', display: 'flex', flexDirection: 'column' }}>
                  <div>⏱️ Dwell Time: <strong>30m 05s</strong> (Required: 30m) ✓</div>
                  <div>📱 Client Verification: <strong>WhatsApp OTP #7214 Verified</strong> ✓</div>
                  <div>📷 Photo Proof: <strong>Counter Photo Verified</strong> ✓</div>
                </div>
              </div>

              {/* Card 3: City Care Clinic (Active In Progress) */}
              <div style={{ ...fieldCardStyle, borderColor: '#3b82f6', background: 'rgba(30, 58, 138, 0.25)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#60a5fa', letterSpacing: '0.5px' }}>STOP #3 • CLINIC</span>
                  <span style={{ background: '#2563eb', color: '#ffffff', fontSize: '11px', fontWeight: 700, padding: '3px 8px', borderRadius: '6px' }}>DWELL IN PROGRESS</span>
                </div>
                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>City Care Diagnostics</h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 12px 0' }}>Rep: Priya Sharma • Contact: Dr. Neha Verma</p>
                <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', fontSize: '12px', color: '#cbd5e1', gap: '6px', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ color: '#60a5fa', fontWeight: 700 }}>⏳ Dwell: 18m 42s elapsed (11m 18s remaining)</div>
                  <div>📍 Location: Verified inside 75m geofence</div>
                  <div>🔒 Anti-Drive-By Lock: Visit cannot close until 30m</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: MILEAGE & REIMBURSEMENT APPROVALS */}
        {activeTab === 'reimbursements' && (
          <div>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                Travel Mileage & Expense Approvals
              </h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                Review employee vehicle travel claims cross-checked against background GPS breadcrumb polylines.
              </p>
            </div>

            <div style={{ background: '#0f172a', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                    <th style={{ padding: '16px 20px' }}>Employee</th>
                    <th style={{ padding: '16px 20px' }}>Mode</th>
                    <th style={{ padding: '16px 20px' }}>Date</th>
                    <th style={{ padding: '16px 20px' }}>Odometer Km</th>
                    <th style={{ padding: '16px 20px' }}>GPS Breadcrumb Km</th>
                    <th style={{ padding: '16px 20px' }}>Discrepancy</th>
                    <th style={{ padding: '16px 20px' }}>Claim Amount</th>
                    <th style={{ padding: '16px 20px' }}>Status</th>
                    <th style={{ padding: '16px 20px', textAlign: 'center' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {claimsList.map(claim => (
                    <tr key={claim.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '16px 20px', fontWeight: 700, color: '#f8fafc' }}>{claim.employeeName}</td>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{claim.mode.replace('_', ' ')}</td>
                      <td style={{ padding: '16px 20px', color: '#94a3b8' }}>{claim.date}</td>
                      <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono, monospace' }}>{claim.odoDistanceKm} km</td>
                      <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono, monospace', color: '#60a5fa' }}>{claim.gpsDistanceKm} km</td>
                      <td style={{ padding: '16px 20px' }}>
                        {claim.isFlagged ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: 700 }}>
                            <AlertTriangle size={14} color="#ef4444" /> {claim.discrepancyPct}% (Fraud Alert)
                          </span>
                        ) : (
                          <span style={{ color: '#86efac', fontSize: '12px', fontWeight: 600 }}>{claim.discrepancyPct}% (Normal)</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px', fontWeight: 700, color: '#f8fafc' }}>₹{claim.totalAmount}</td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: '999px',
                          fontSize: '11px',
                          fontWeight: 700,
                          background: claim.status === 'APPROVED' ? 'rgba(34, 197, 94, 0.2)' : claim.status === 'REJECTED' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                          color: claim.status === 'APPROVED' ? '#4ade80' : claim.status === 'REJECTED' ? '#fca5a5' : '#fde047',
                        }}>
                          {claim.status}
                        </span>
                      </td>
                      <td style={{ padding: '16px 20px', textAlign: 'center' }}>
                        {claim.status === 'PENDING' ? (
                          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                            <button
                              onClick={() => handleClaimAction(claim.id, 'APPROVED')}
                              style={{ background: '#16a34a', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 700 }}
                            >
                              <Check size={14} /> Approve
                            </button>
                            <button
                              onClick={() => handleClaimAction(claim.id, 'REJECTED')}
                              style={{ background: '#dc2626', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 700 }}
                            >
                              <X size={14} /> Reject
                            </button>
                          </div>
                        ) : (
                          <span style={{ fontSize: '12px', color: '#64748b' }}>Reviewed</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: TENANT POLICY CONFIGURATION */}
        {activeTab === 'policy' && (
          <div style={{ maxWidth: '640px' }}>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                Employer Policy Configuration
              </h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                Configure rules for field visit dwell enforcement, travel reimbursement rates, and anti-fraud thresholds.
              </p>
            </div>

            <div style={{ background: '#0f172a', borderRadius: '20px', padding: '28px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={labelStyle}>Default Field Visit Dwell Time (Minutes)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    type="number"
                    value={defaultDwellMins}
                    onChange={e => setDefaultDwellMins(Number(e.target.value))}
                    style={inputStyle}
                    min={5}
                    max={120}
                  />
                  <span style={{ fontSize: '13px', color: '#94a3b8' }}>Minutes required before visit completes (Default: 30)</span>
                </div>
              </div>

              <div>
                <label style={labelStyle}>Personal Car Reimbursement Rate (INR / km)</label>
                <input
                  type="number"
                  step="0.5"
                  value={carRate}
                  onChange={e => setCarRate(Number(e.target.value))}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Two-Wheeler Reimbursement Rate (INR / km)</label>
                <input
                  type="number"
                  step="0.5"
                  value={bikeRate}
                  onChange={e => setBikeRate(Number(e.target.value))}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Odometer vs GPS Discrepancy Alert Threshold (%)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    type="number"
                    value={discrepancyThreshold}
                    onChange={e => setDiscrepancyThreshold(Number(e.target.value))}
                    style={inputStyle}
                    min={5}
                    max={50}
                  />
                  <span style={{ fontSize: '13px', color: '#94a3b8' }}>Gaps above this threshold trigger a fraud alert</span>
                </div>
              </div>

              <button
                onClick={handleSavePolicy}
                style={{
                  background: policySaved ? '#16a34a' : '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  padding: '12px 20px',
                  borderRadius: '12px',
                  fontWeight: 700,
                  fontSize: '14px',
                  cursor: 'pointer',
                  marginTop: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {policySaved ? <Check size={18} /> : null}
                {policySaved ? 'Policy Settings Saved!' : 'Save Policy Changes'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

const kpiCardStyle: React.CSSProperties = {
  background: '#0f172a',
  borderRadius: '18px',
  padding: '20px',
  border: '1px solid rgba(255, 255, 255, 0.08)',
};

const fieldCardStyle: React.CSSProperties = {
  background: '#0f172a',
  borderRadius: '18px',
  padding: '20px',
  border: '1px solid rgba(255, 255, 255, 0.08)',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '13px',
  fontWeight: 600,
  color: '#cbd5e1',
  marginBottom: '8px',
};

const inputStyle: React.CSSProperties = {
  background: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '10px',
  padding: '10px 14px',
  color: '#ffffff',
  fontSize: '15px',
  width: '140px',
  outline: 'none',
};
