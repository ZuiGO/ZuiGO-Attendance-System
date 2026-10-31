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
  UserPlus,
  Trash2,
  Briefcase,
  Wifi,
  Smartphone,
  Activity,
  Plus,
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
  presenceType: 'IN_OFFICE' | 'ON_FIELD_VISIT' | 'TRAVEL_SHIFT' | 'ABSENT';
  networkType: 'OFFICE_WIFI' | 'PERSONAL_CELLULAR' | 'OFFLINE';
  isOfficeWifi: boolean;
  liveLocation?: string;
  lastSeenAt?: string;
}

interface EmployeeRecord {
  id: string;
  name: string;
  code: string;
  email: string;
  phone?: string;
  department: string;
  role: string;
  device?: string;
  isActive: boolean;
}

interface AdminTask {
  id: string;
  title: string;
  projectName: string;
  assignedToName: string;
  priority: string;
  status: string;
  estimatedHours: number;
  activeStopwatchRunning: boolean;
  activeSeconds: number;
}

interface ActivityLog {
  id: string;
  timestamp: string;
  employeeName: string;
  employeeCode: string;
  activityType: string;
  description: string;
  networkType: string;
  isOfficeWifi: boolean;
  location?: string;
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
    office: 'Cyber City HQ (Floor 4)',
    clockInTime: '09:02 AM',
    currentTask: 'Implement On-Device Liveness Verification',
    taskDurationSec: 3240,
    status: 'WORKING',
    presenceType: 'IN_OFFICE',
    networkType: 'OFFICE_WIFI',
    isOfficeWifi: true,
    liveLocation: 'Cyber City HQ (28.498, 77.089)',
    lastSeenAt: 'Just now',
  },
  {
    id: 'emp-2',
    name: 'Priya Sharma',
    code: 'EMP-1002',
    department: 'Hospital Relations',
    office: 'Cyber City HQ (Floor 4)',
    clockInTime: '08:55 AM',
    currentTask: 'Apollo Hospital Beat Visit',
    taskDurationSec: 4120,
    status: 'WORKING',
    presenceType: 'ON_FIELD_VISIT',
    networkType: 'PERSONAL_CELLULAR',
    isOfficeWifi: false,
    liveLocation: 'Apollo City Hospital (28.535, 77.260)',
    lastSeenAt: '1 min ago',
  },
  {
    id: 'emp-3',
    name: 'Rahul Verma',
    code: 'EMP-1003',
    department: 'Field Operations',
    office: 'Noida Branch',
    clockInTime: '09:14 AM',
    currentTask: 'Highway Transit to Distributor',
    taskDurationSec: 1800,
    status: 'WORKING',
    presenceType: 'TRAVEL_SHIFT',
    networkType: 'PERSONAL_CELLULAR',
    isOfficeWifi: false,
    liveLocation: 'Sector 62 Expressway (28.628, 77.364)',
    lastSeenAt: '30s ago',
  },
  {
    id: 'emp-4',
    name: 'Sneha Patel',
    code: 'EMP-1004',
    department: 'Product Operations',
    office: 'Cyber City HQ (Floor 4)',
    clockInTime: 'Not Clocked In',
    currentTask: null,
    taskDurationSec: 0,
    status: 'IDLE',
    presenceType: 'ABSENT',
    networkType: 'OFFLINE',
    isOfficeWifi: false,
    liveLocation: 'Offline',
    lastSeenAt: 'Yesterday 18:30',
  },
];

const INITIAL_EMPLOYEES: EmployeeRecord[] = [
  { id: 'emp-0', name: 'Jayesh Admin', code: 'EMP-001', email: 'jayesh@zuigo.ai', phone: '+919800000001', department: 'Engineering', role: 'ADMIN', device: 'DEV-WORKSTATION-01', isActive: true },
  { id: 'emp-1', name: 'Alex Johnson', code: 'EMP-1001', email: 'alex.j@zuigo.ai', phone: '+919800001001', department: 'Engineering', role: 'EMPLOYEE', device: 'DEV-PIXEL-7-PRO-SECURE', isActive: true },
  { id: 'emp-2', name: 'Priya Sharma', code: 'EMP-1002', email: 'priya.s@zuigo.ai', phone: '+919800001002', department: 'Hospital Relations', role: 'EMPLOYEE', device: 'DEV-SAMSUNG-S23-ULTRA', isActive: true },
  { id: 'emp-3', name: 'Rahul Verma', code: 'EMP-1003', email: 'rahul.v@zuigo.ai', phone: '+919800001003', department: 'Field Operations', role: 'MANAGER', device: 'DEV-ONEPLUS-11-CORP', isActive: true },
];

const INITIAL_TASKS: AdminTask[] = [
  { id: 't-1', title: 'Implement On-Device Liveness Verification', projectName: 'Mobile App V2', assignedToName: 'Alex Johnson', priority: 'HIGH', status: 'IN_PROGRESS', estimatedHours: 4.0, activeStopwatchRunning: true, activeSeconds: 3240 },
  { id: 't-2', title: 'Apollo Hospital Beat Visit & Demo Kit', projectName: 'Client Field Visits', assignedToName: 'Priya Sharma', priority: 'URGENT', status: 'IN_PROGRESS', estimatedHours: 3.0, activeStopwatchRunning: true, activeSeconds: 4120 },
  { id: 't-3', title: 'Highway Transit to Distributor', projectName: 'Logistics', assignedToName: 'Rahul Verma', priority: 'MEDIUM', status: 'IN_PROGRESS', estimatedHours: 2.0, activeStopwatchRunning: true, activeSeconds: 1800 },
];

const INITIAL_LOGS: ActivityLog[] = [
  { id: 'log-1', timestamp: 'Today 09:02 AM', employeeName: 'Alex Johnson', employeeCode: 'EMP-1001', activityType: 'CLOCK_IN', description: 'Zero-trust QR attendance verified via Office Wi-Fi (BSSID 3c:37:12:89:af:90)', networkType: 'OFFICE_WIFI', isOfficeWifi: true, location: 'Cyber City HQ' },
  { id: 'log-2', timestamp: 'Today 09:03 AM', employeeName: 'Alex Johnson', employeeCode: 'EMP-1001', activityType: 'TASK_STARTED', description: 'Started stopwatch on task: Implement On-Device Liveness Verification', networkType: 'OFFICE_WIFI', isOfficeWifi: true, location: 'Cyber City HQ' },
  { id: 'log-3', timestamp: 'Today 09:15 AM', employeeName: 'Priya Sharma', employeeCode: 'EMP-1002', activityType: 'FIELD_VISIT_ARRIVAL', description: 'Arrived at Apollo City Hospital (geofence < 75m confirmed). 30-min dwell timer started.', networkType: 'PERSONAL_CELLULAR', isOfficeWifi: false, location: 'Apollo City Hospital' },
  { id: 'log-4', timestamp: 'Today 09:47 AM', employeeName: 'Priya Sharma', employeeCode: 'EMP-1002', activityType: 'FIELD_VISIT_COMPLETED', description: 'Client SMS OTP #4921 verified with Dr. Sharma. Photo proof uploaded.', networkType: 'PERSONAL_CELLULAR', isOfficeWifi: false, location: 'Apollo City Hospital' },
];

const INITIAL_CLAIMS: TravelClaim[] = [
  { id: 'tc-1', employeeName: 'Priya Sharma', mode: 'PERSONAL_CAR', date: '2026-10-30', odoDistanceKm: 42.7, gpsDistanceKm: 41.3, discrepancyPct: 3.39, isFlagged: false, ratePerKm: 8.0, totalAmount: 330.4, status: 'PENDING' },
  { id: 'tc-2', employeeName: 'Vikram Singh', mode: 'PERSONAL_CAR', date: '2026-10-29', odoDistanceKm: 58.0, gpsDistanceKm: 38.2, discrepancyPct: 34.14, isFlagged: true, ratePerKm: 8.0, totalAmount: 305.6, status: 'PENDING' },
  { id: 'tc-3', employeeName: 'Amit Joshi', mode: 'TWO_WHEELER', date: '2026-10-29', odoDistanceKm: 24.5, gpsDistanceKm: 23.8, discrepancyPct: 2.86, isFlagged: false, ratePerKm: 4.0, totalAmount: 95.2, status: 'APPROVED' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'presence' | 'employees' | 'tasks' | 'activity' | 'field' | 'reimbursements' | 'policy'>('presence');
  const [presenceList, setPresenceList] = useState<EmployeePresence[]>(INITIAL_PRESENCE);
  const [employeeList, setEmployeeList] = useState<EmployeeRecord[]>(INITIAL_EMPLOYEES);
  const [taskList, setTaskList] = useState<AdminTask[]>(INITIAL_TASKS);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>(INITIAL_LOGS);
  const [claimsList, setClaimsList] = useState<TravelClaim[]>(INITIAL_CLAIMS);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [showAddEmployeeModal, setShowAddEmployeeModal] = useState(false);
  const [newEmpName, setNewEmpName] = useState('');
  const [newEmpEmail, setNewEmpEmail] = useState('');
  const [newEmpPassword, setNewEmpPassword] = useState('');
  const [newEmpCode, setNewEmpCode] = useState('');
  const [newEmpRole, setNewEmpRole] = useState('EMPLOYEE');
  const [newEmpDept, setNewEmpDept] = useState('Field Operations');
  const [newEmpPhone, setNewEmpPhone] = useState('');

  const [showAssignTaskModal, setShowAssignTaskModal] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskAssignee, setNewTaskAssignee] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('MEDIUM');
  const [newTaskHours, setNewTaskHours] = useState('3.0');
  const [newTaskDesc, setNewTaskDesc] = useState('');

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
          item.status === 'WORKING' && item.currentTask
            ? { ...item, taskDurationSec: item.taskDurationSec + 1 }
            : item
        )
      );
      setTaskList(prev =>
        prev.map(task =>
          task.activeStopwatchRunning
            ? { ...task, activeSeconds: task.activeSeconds + 1 }
            : task
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

  const handleAddEmployee = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmpName || !newEmpEmail || !newEmpCode) return;

    const newEmp: EmployeeRecord = {
      id: 'emp-' + Date.now(),
      name: newEmpName,
      code: newEmpCode,
      email: newEmpEmail,
      phone: newEmpPhone || undefined,
      department: newEmpDept,
      role: newEmpRole,
      device: undefined,
      isActive: true,
    };

    setEmployeeList(prev => [...prev, newEmp]);

    // Also add to presence list as absent initially
    setPresenceList(prev => [
      ...prev,
      {
        id: newEmp.id,
        name: newEmp.name,
        code: newEmp.code,
        department: newEmp.department,
        office: 'Cyber City HQ',
        clockInTime: 'Not Clocked In',
        currentTask: null,
        taskDurationSec: 0,
        status: 'IDLE',
        presenceType: 'ABSENT',
        networkType: 'OFFLINE',
        isOfficeWifi: false,
        liveLocation: 'Offline',
        lastSeenAt: 'Just created',
      },
    ]);

    // Add activity log
    setActivityLogs(prev => [
      {
        id: 'log-' + Date.now(),
        timestamp: 'Just now',
        employeeName: newEmp.name,
        employeeCode: newEmp.code,
        activityType: 'EMPLOYEE_CREATED',
        description: `Enrolled new employee ${newEmp.name} in department ${newEmp.department} (${newEmp.role})`,
        networkType: 'OFFICE_WIFI',
        isOfficeWifi: true,
        location: 'Admin Portal',
      },
      ...prev,
    ]);

    setShowAddEmployeeModal(false);
    setNewEmpName('');
    setNewEmpEmail('');
    setNewEmpPassword('');
    setNewEmpCode('');
    setNewEmpPhone('');
  };

  const handleDeleteEmployee = (id: string, name: string) => {
    if (!confirm(`Are you sure you want to deactivate ${name}?`)) return;

    setEmployeeList(prev =>
      prev.map(e => (e.id === id ? { ...e, isActive: false } : e))
    );

    setPresenceList(prev =>
      prev.map(p =>
        p.id === id
          ? { ...p, status: 'IDLE', presenceType: 'ABSENT', currentTask: null }
          : p
      )
    );

    setActivityLogs(prev => [
      {
        id: 'log-' + Date.now(),
        timestamp: 'Just now',
        employeeName: name,
        employeeCode: id,
        activityType: 'EMPLOYEE_DEACTIVATED',
        description: `Deactivated employee ${name} from active operations`,
        networkType: 'OFFICE_WIFI',
        isOfficeWifi: true,
        location: 'Admin Portal',
      },
      ...prev,
    ]);
  };

  const handleAssignTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle) return;

    const assignedEmp = employeeList.find(e => e.id === newTaskAssignee) || employeeList[1];

    const newTask: AdminTask = {
      id: 'task-' + Date.now(),
      title: newTaskTitle,
      projectName: 'Field Operations',
      assignedToName: assignedEmp.name,
      priority: newTaskPriority,
      status: 'TODO',
      estimatedHours: parseFloat(newTaskHours) || 3.0,
      activeStopwatchRunning: false,
      activeSeconds: 0,
    };

    setTaskList(prev => [newTask, ...prev]);

    setActivityLogs(prev => [
      {
        id: 'log-' + Date.now(),
        timestamp: 'Just now',
        employeeName: assignedEmp.name,
        employeeCode: assignedEmp.code,
        activityType: 'TASK_ASSIGNED',
        description: `Assigned task "${newTask.title}" with priority ${newTask.priority}`,
        networkType: 'OFFICE_WIFI',
        isOfficeWifi: true,
        location: 'Admin Portal',
      },
      ...prev,
    ]);

    setShowAssignTaskModal(false);
    setNewTaskTitle('');
    setNewTaskDesc('');
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#090d16', color: '#f8fafc' }}>
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
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Organization: ZuiGO Technologies Inc.</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '6px', background: '#0f172a', padding: '4px', borderRadius: '12px' }}>
          <button
            onClick={() => setActiveTab('presence')}
            style={tabButtonStyle(activeTab === 'presence')}
          >
            <Users size={16} /> Live Presence
          </button>
          <button
            onClick={() => setActiveTab('employees')}
            style={tabButtonStyle(activeTab === 'employees')}
          >
            <UserPlus size={16} /> Employees
          </button>
          <button
            onClick={() => setActiveTab('tasks')}
            style={tabButtonStyle(activeTab === 'tasks')}
          >
            <Briefcase size={16} /> Tasks
          </button>
          <button
            onClick={() => setActiveTab('activity')}
            style={tabButtonStyle(activeTab === 'activity')}
          >
            <Activity size={16} /> Activity Logs
          </button>
          <button
            onClick={() => setActiveTab('field')}
            style={tabButtonStyle(activeTab === 'field')}
          >
            <MapPin size={16} /> Field Beats
          </button>
          <button
            onClick={() => setActiveTab('reimbursements')}
            style={tabButtonStyle(activeTab === 'reimbursements')}
          >
            <Car size={16} /> Mileage & Claims
          </button>
          <button
            onClick={() => setActiveTab('policy')}
            style={tabButtonStyle(activeTab === 'policy')}
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '28px' }}>
              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600 }}>Total Present</div>
                <div style={{ fontSize: '28px', fontWeight: 800, color: '#4ade80', margin: '4px 0' }}>3</div>
                <div style={{ fontSize: '11px', color: '#86efac' }}>75% of workforce</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600 }}>Office Wi-Fi</div>
                <div style={{ fontSize: '28px', fontWeight: 800, color: '#60a5fa', margin: '4px 0' }}>1</div>
                <div style={{ fontSize: '11px', color: '#93c5fd' }}>Verified BSSID geofence</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600 }}>Personal Cellular</div>
                <div style={{ fontSize: '28px', fontWeight: 800, color: '#fbbf24', margin: '4px 0' }}>2</div>
                <div style={{ fontSize: '11px', color: '#fde047' }}>Mobile data / outside</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600 }}>On Field Beat</div>
                <div style={{ fontSize: '28px', fontWeight: 800, color: '#c084fc', margin: '4px 0' }}>1</div>
                <div style={{ fontSize: '11px', color: '#e9d5ff' }}>Hospital client dwell</div>
              </div>

              <div style={kpiCardStyle}>
                <div style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 600 }}>Currently Absent</div>
                <div style={{ fontSize: '28px', fontWeight: 800, color: '#f87171', margin: '4px 0' }}>1</div>
                <div style={{ fontSize: '11px', color: '#fca5a5' }}>Not clocked in today</div>
              </div>
            </div>

            {/* Filter and Search Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: '#0f172a', padding: '10px 16px', borderRadius: '12px', border: '1px solid #334155', width: '380px' }}>
                <Search size={18} color="#64748b" />
                <input
                  type="text"
                  placeholder="Search employee, task, department..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{ background: 'transparent', border: 'none', color: '#ffffff', outline: 'none', fontSize: '14px', width: '100%' }}
                />
              </div>

              <div style={{ fontSize: '13px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }} />
                Real-time presence updates ticking live
              </div>
            </div>

            {/* Live Table */}
            <div style={{ background: '#0f172a', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                    <th style={{ padding: '16px 20px' }}>Employee</th>
                    <th style={{ padding: '16px 20px' }}>Department & Office</th>
                    <th style={{ padding: '16px 20px' }}>Presence State</th>
                    <th style={{ padding: '16px 20px' }}>Network Connection</th>
                    <th style={{ padding: '16px 20px' }}>Current Activity</th>
                    <th style={{ padding: '16px 20px' }}>Stopwatch Ticker</th>
                    <th style={{ padding: '16px 20px' }}>Live Location</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPresence.map(row => (
                    <tr key={row.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontWeight: 700, color: '#f8fafc' }}>{row.name}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{row.code}</div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ color: '#cbd5e1' }}>{row.department}</div>
                        <div style={{ fontSize: '12px', color: '#94a3b8' }}>{row.office}</div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        {row.presenceType === 'IN_OFFICE' && <span style={tagStyle('#22c55e')}>🏢 IN OFFICE</span>}
                        {row.presenceType === 'ON_FIELD_VISIT' && <span style={tagStyle('#a855f7')}>📍 FIELD VISIT</span>}
                        {row.presenceType === 'TRAVEL_SHIFT' && <span style={tagStyle('#3b82f6')}>🚗 IN TRANSIT</span>}
                        {row.presenceType === 'ABSENT' && <span style={tagStyle('#ef4444')}>❌ ABSENT</span>}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        {row.isOfficeWifi ? (
                          <span style={tagStyle('#22c55e')}>📶 Office Wi-Fi</span>
                        ) : row.networkType === 'PERSONAL_CELLULAR' ? (
                          <span style={tagStyle('#eab308')}>📱 Personal Internet</span>
                        ) : (
                          <span style={tagStyle('#64748b')}>Offline</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        {row.currentTask ? (
                          <span style={{ color: '#93c5fd', fontWeight: 600 }}>{row.currentTask}</span>
                        ) : (
                          <span style={{ color: '#64748b' }}>No active task</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#f8fafc' }}>
                        {row.taskDurationSec > 0 ? (
                          <span style={{ color: '#4ade80' }}>⏱️ {formatSeconds(row.taskDurationSec)}</span>
                        ) : '—'}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontSize: '13px', color: '#cbd5e1' }}>{row.liveLocation || 'Cyber City HQ'}</div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>Last seen: {row.lastSeenAt}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: EMPLOYEE MANAGEMENT */}
        {activeTab === 'employees' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                  Employee Directory & Identity Management
                </h2>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                  Enroll workforce personnel, manage hardware device bindings, and deactivate departed accounts.
                </p>
              </div>
              <button
                onClick={() => setShowAddEmployeeModal(true)}
                style={primaryBtnStyle}
              >
                <Plus size={16} /> Add New Employee
              </button>
            </div>

            <div style={{ background: '#0f172a', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                    <th style={{ padding: '16px 20px' }}>Employee</th>
                    <th style={{ padding: '16px 20px' }}>Email & Phone</th>
                    <th style={{ padding: '16px 20px' }}>Department</th>
                    <th style={{ padding: '16px 20px' }}>Role</th>
                    <th style={{ padding: '16px 20px' }}>Hardware Device Binding</th>
                    <th style={{ padding: '16px 20px' }}>Status</th>
                    <th style={{ padding: '16px 20px', textAlign: 'center' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {employeeList.map(emp => (
                    <tr key={emp.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontWeight: 700, color: '#f8fafc' }}>{emp.name}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{emp.code}</div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <div>{emp.email}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{emp.phone || '--'}</div>
                      </td>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{emp.department}</td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={tagStyle(emp.role === 'ADMIN' ? '#c084fc' : '#60a5fa')}>{emp.role}</span>
                      </td>
                      <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono, monospace', fontSize: '12px' }}>
                        {emp.device ? (
                          <span style={{ color: '#4ade80' }}>🔒 {emp.device}</span>
                        ) : (
                          <span style={{ color: '#94a3b8' }}>Pending Binding</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={tagStyle(emp.isActive ? '#22c55e' : '#ef4444')}>
                          {emp.isActive ? 'ACTIVE' : 'DEACTIVATED'}
                        </span>
                      </td>
                      <td style={{ padding: '16px 20px', textAlign: 'center' }}>
                        {emp.isActive && emp.role !== 'ADMIN' ? (
                          <button
                            onClick={() => handleDeleteEmployee(emp.id, emp.name)}
                            style={{
                              background: 'rgba(239, 68, 68, 0.15)',
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              color: '#f87171',
                              padding: '6px 12px',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: '12px',
                              fontWeight: 600,
                            }}
                          >
                            <Trash2 size={14} /> Deactivate
                          </button>
                        ) : (
                          <span style={{ fontSize: '12px', color: '#64748b' }}>Protected</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: TASK ASSIGNMENT */}
        {activeTab === 'tasks' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                  Task Assignment & Real-Time Stopwatch Monitor
                </h2>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                  Assign operational tasks to staff. Track live ticking stopwatches attendance-gated to verified physical check-ins.
                </p>
              </div>
              <button
                onClick={() => setShowAssignTaskModal(true)}
                style={primaryBtnStyle}
              >
                <Plus size={16} /> Assign New Task
              </button>
            </div>

            <div style={{ background: '#0f172a', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                    <th style={{ padding: '16px 20px' }}>Task Title & Project</th>
                    <th style={{ padding: '16px 20px' }}>Assigned Employee</th>
                    <th style={{ padding: '16px 20px' }}>Priority</th>
                    <th style={{ padding: '16px 20px' }}>Estimated Hours</th>
                    <th style={{ padding: '16px 20px' }}>Live Stopwatch Status</th>
                    <th style={{ padding: '16px 20px' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {taskList.map(task => (
                    <tr key={task.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontWeight: 700, color: '#f8fafc' }}>{task.title}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>Project: {task.projectName}</div>
                      </td>
                      <td style={{ padding: '16px 20px', fontWeight: 600, color: '#cbd5e1' }}>
                        {task.assignedToName}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={tagStyle(task.priority === 'URGENT' || task.priority === 'HIGH' ? '#f59e0b' : '#3b82f6')}>
                          {task.priority}
                        </span>
                      </td>
                      <td style={{ padding: '16px 20px', fontFamily: 'JetBrains Mono, monospace' }}>
                        {task.estimatedHours} hrs
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        {task.activeStopwatchRunning ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#4ade80', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                            <Clock size={16} /> TICKING ({formatSeconds(task.activeSeconds)})
                          </span>
                        ) : (
                          <span style={{ color: '#64748b' }}>Idle</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={tagStyle(task.status === 'IN_PROGRESS' ? '#3b82f6' : '#22c55e')}>
                          {task.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: ACTIVITY AUDIT TRAIL */}
        {activeTab === 'activity' && (
          <div>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                Immutable User Activity Audit Trail
              </h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                Complete chronological log of employee actions: Clock-ins, Clock-outs, Stopwatches, Field OTPs, and Network connection types.
              </p>
            </div>

            <div style={{ background: '#0f172a', borderRadius: '18px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                    <th style={{ padding: '16px 20px' }}>Timestamp</th>
                    <th style={{ padding: '16px 20px' }}>Employee</th>
                    <th style={{ padding: '16px 20px' }}>Event</th>
                    <th style={{ padding: '16px 20px' }}>Description & Details</th>
                    <th style={{ padding: '16px 20px' }}>Network Verified</th>
                    <th style={{ padding: '16px 20px' }}>Location</th>
                  </tr>
                </thead>
                <tbody>
                  {activityLogs.map(log => (
                    <tr key={log.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '16px 20px', fontSize: '13px', color: '#94a3b8' }}>{log.timestamp}</td>
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontWeight: 700, color: '#f8fafc' }}>{log.employeeName}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{log.employeeCode}</div>
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={tagStyle(log.activityType.includes('CLOCK') ? '#22c55e' : log.activityType.includes('FIELD') ? '#c084fc' : '#3b82f6')}>
                          {log.activityType}
                        </span>
                      </td>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{log.description}</td>
                      <td style={{ padding: '16px 20px' }}>
                        {log.isOfficeWifi ? (
                          <span style={tagStyle('#22c55e')}>📶 Office Wi-Fi</span>
                        ) : (
                          <span style={tagStyle('#eab308')}>📱 Personal Internet</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px', color: '#94a3b8', fontSize: '12px' }}>{log.location || 'Cyber City HQ'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 5: FIELD BEAT & ROUTE MONITORING */}
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
              <div style={fieldCardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8' }}>STOP #1 • HOSPITAL</span>
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

              <div style={fieldCardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8' }}>STOP #2 • DISTRIBUTOR</span>
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

              <div style={{ ...fieldCardStyle, borderColor: '#3b82f6', background: 'rgba(30, 58, 138, 0.25)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#60a5fa' }}>STOP #3 • CLINIC</span>
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

        {/* TAB 6: MILEAGE & REIMBURSEMENT APPROVALS */}
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
                        <span style={tagStyle(claim.status === 'APPROVED' ? '#22c55e' : claim.status === 'REJECTED' ? '#ef4444' : '#eab308')}>
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

        {/* TAB 7: TENANT POLICY CONFIGURATION */}
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

      {/* MODAL: ADD EMPLOYEE */}
      {showAddEmployeeModal && (
        <div style={modalOverlayStyle}>
          <div style={modalCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Enroll New Employee</h3>
              <button onClick={() => setShowAddEmployeeModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>
            <form onSubmit={handleAddEmployee}>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Full Name *</label>
                <input type="text" value={newEmpName} onChange={e => setNewEmpName(e.target.value)} required placeholder="e.g. Sarah Connor" style={{ ...inputStyle, width: '100%' }} />
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Email Address *</label>
                <input type="email" value={newEmpEmail} onChange={e => setNewEmpEmail(e.target.value)} required placeholder="sarah@zuigo.ai" style={{ ...inputStyle, width: '100%' }} />
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Temporary Password *</label>
                <input type="password" value={newEmpPassword} onChange={e => setNewEmpPassword(e.target.value)} required placeholder="At least 6 characters" style={{ ...inputStyle, width: '100%' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={labelStyle}>Employee Code *</label>
                  <input type="text" value={newEmpCode} onChange={e => setNewEmpCode(e.target.value)} required placeholder="EMP-1005" style={{ ...inputStyle, width: '100%' }} />
                </div>
                <div>
                  <label style={labelStyle}>Role</label>
                  <select value={newEmpRole} onChange={e => setNewEmpRole(e.target.value)} style={{ ...inputStyle, width: '100%' }}>
                    <option value="EMPLOYEE">EMPLOYEE</option>
                    <option value="MANAGER">MANAGER</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </div>
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Department</label>
                <select value={newEmpDept} onChange={e => setNewEmpDept(e.target.value)} style={{ ...inputStyle, width: '100%' }}>
                  <option value="Field Operations">Field Operations</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Hospital Relations">Hospital Relations</option>
                  <option value="Customer Success">Customer Success</option>
                  <option value="Operations">Operations</option>
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button type="button" onClick={() => setShowAddEmployeeModal(false)} style={{ background: '#334155', border: 'none', color: '#fff', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={primaryBtnStyle}>Enroll Employee</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ASSIGN TASK */}
      {showAssignTaskModal && (
        <div style={modalOverlayStyle}>
          <div style={modalCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Assign Operational Task</h3>
              <button onClick={() => setShowAssignTaskModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>
            <form onSubmit={handleAssignTask}>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Task Title *</label>
                <input type="text" value={newTaskTitle} onChange={e => setNewTaskTitle(e.target.value)} required placeholder="e.g. Deploy Sensor Firmware" style={{ ...inputStyle, width: '100%' }} />
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Assign To Employee *</label>
                <select value={newTaskAssignee} onChange={e => setNewTaskAssignee(e.target.value)} style={{ ...inputStyle, width: '100%' }}>
                  {employeeList.filter(e => e.isActive).map(e => (
                    <option key={e.id} value={e.id}>{e.name} ({e.code} - {e.department})</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={labelStyle}>Priority</label>
                  <select value={newTaskPriority} onChange={e => setNewTaskPriority(e.target.value)} style={{ ...inputStyle, width: '100%' }}>
                    <option value="HIGH">HIGH</option>
                    <option value="URGENT">URGENT</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Estimated Hours</label>
                  <input type="number" step="0.5" value={newTaskHours} onChange={e => setNewTaskHours(e.target.value)} style={{ ...inputStyle, width: '100%' }} />
                </div>
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={labelStyle}>Instructions</label>
                <textarea value={newTaskDesc} onChange={e => setNewTaskDesc(e.target.value)} placeholder="Task details..." style={{ ...inputStyle, width: '100%', height: '80px', resize: 'none' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button type="button" onClick={() => setShowAssignTaskModal(false)} style={{ background: '#334155', border: 'none', color: '#fff', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={primaryBtnStyle}>Assign Task</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const tabButtonStyle = (isActive: boolean): React.CSSProperties => ({
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '8px 14px',
  borderRadius: '8px',
  border: 'none',
  cursor: 'pointer',
  fontSize: '13px',
  fontWeight: 600,
  background: isActive ? '#2563eb' : 'transparent',
  color: isActive ? '#ffffff' : '#94a3b8',
  transition: 'all 0.15s ease',
});

const tagStyle = (color: string): React.CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  padding: '4px 10px',
  borderRadius: '999px',
  fontSize: '11px',
  fontWeight: 700,
  background: `${color}25`,
  color: color,
  border: `1px solid ${color}40`,
});

const kpiCardStyle: React.CSSProperties = {
  background: '#0f172a',
  borderRadius: '16px',
  padding: '16px 20px',
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
  fontSize: '12px',
  fontWeight: 600,
  color: '#cbd5e1',
  marginBottom: '6px',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const inputStyle: React.CSSProperties = {
  background: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '10px',
  padding: '10px 14px',
  color: '#ffffff',
  fontSize: '14px',
  outline: 'none',
  boxSizing: 'border-box',
};

const primaryBtnStyle: React.CSSProperties = {
  background: '#2563eb',
  color: '#ffffff',
  border: 'none',
  padding: '10px 18px',
  borderRadius: '10px',
  fontWeight: 700,
  fontSize: '13px',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '6px',
};

const modalOverlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(0, 0, 0, 0.75)',
  backdropFilter: 'blur(8px)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 100,
};

const modalCardStyle: React.CSSProperties = {
  background: '#0f172a',
  border: '1px solid rgba(255, 255, 255, 0.12)',
  borderRadius: '18px',
  padding: '28px',
  width: '100%',
  maxWidth: '480px',
  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
};
