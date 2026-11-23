import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { 
  ChevronRight, 
  AlertCircle, 
  AlertTriangle, 
  Plus, 
  CheckCircle2, 
  Users, 
  FileText, 
  TrendingUp, 
  CheckCircle, 
  Search, 
  ChevronDown, 
  Calendar, 
  User, 
  Phone, 
  X, 
  Check, 
  UserCheck, 
  FlaskConical, 
  Clock, 
  BarChart3, 
  Download, 
  Eye, 
  FileDown, 
  Upload, 
  RefreshCw, 
  Play, 
  Database, 
  ArrowRight, 
  ShieldCheck, 
  History, 
  FileSpreadsheet 
} from 'lucide-react';
import { reportAnalyzerApi } from './reportAnalyzerApi';
import ParameterTrendChart from './ParameterTrendChart';

/* =========================================================================
   1. REUSABLE UI BUTTON (Pure Tailwind v4)
   ========================================================================= */
const Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
  const base = 'inline-flex items-center justify-center font-bold rounded-xl transition-all cursor-pointer shadow-2xs select-none disabled:opacity-50 disabled:cursor-not-allowed';
  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-xs',
    lg: 'px-5 py-2.5 text-sm',
  };
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white',
    secondary: 'bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 border border-slate-200',
    danger: 'bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white',
    outline: 'bg-transparent hover:bg-blue-50 text-blue-600 border border-blue-200',
    ghost: 'bg-transparent hover:bg-slate-100 text-slate-600 shadow-none',
  };
  return (
    <button className={`${base} ${sizes[size] || sizes.md} ${variants[variant] || variants.primary} ${className}`} {...props}>
      {children}
    </button>
  );
};

/* ==========================================================================
   2. CLINICAL & FORMATTING HELPERS
   ========================================================================= */
function calculateAge(dobStr) {
  if (!dobStr) return '—';
  try {
    const dob = new Date(dobStr);
    if (isNaN(dob.getTime())) return '—';
    const diffMs = Date.now() - dob.getTime();
    return Math.abs(new Date(diffMs).getUTCFullYear() - 1970);
  } catch {
    return '—';
  }
}

function getInitials(name) {
  if (!name) return '—';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.substring(0, 2).toUpperCase();
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/* =========================================================================
   3. CUSTOM HOOK FOR STATE MANAGEMENT & API INTEGRATION
   ========================================================================= */
const useReportAnalyzer = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [fileSizeStr, setFileSizeStr] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisData, setAnalysisData] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [error, setError] = useState(null);

  // Filters & Search
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Sample Reports
  const [samples, setSamples] = useState([]);
  const [selectedSample, setSelectedSample] = useState('');
  const [isLoadingSample, setIsLoadingSample] = useState(false);

  // Registered Patients & Active Selected Patient
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);

  // Dashboard Top Metrics
  const [metrics, setMetrics] = useState(null);

  // Center Panel Navigation & Date Filter
  const [activeCenterTab, setActiveCenterTab] = useState('lab_results');
  const [selectedDate, setSelectedDate] = useState('');

  // Parameter Trend Modal State (Interactive Line Chart)
  const [graphModalOpen, setGraphModalOpen] = useState(false);
  const [graphParameter, setGraphParameter] = useState(null);

  // Upload & Analysis Modal State
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  // Live MSSQL Database Saved Timeline State
  const [savedTimelineData, setSavedTimelineData] = useState(null);
  const [isFetchingSavedTimeline, setIsFetchingSavedTimeline] = useState(false);
  const [savedTimelineError, setSavedTimelineError] = useState(null);

  // Patient Timeline Modal State (Full Audit Table)
  const [timelineModalOpen, setTimelineModalOpen] = useState(false);
  const [timelineData, setTimelineData] = useState(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState(null);

  // Fetch Live Database Timeline for Verified Patient
  const fetchSavedTimeline = useCallback(async (patientId) => {
    if (!patientId) {
      setSavedTimelineData(null);
      return;
    }
    setIsFetchingSavedTimeline(true);
    setSavedTimelineError(null);
    try {
      const res = await reportAnalyzerApi.getPatientTimeline(patientId);
      if (res.data && res.data.success) {
        setSavedTimelineData(res.data.data);
      } else {
        setSavedTimelineError(res.data?.message || 'Failed to query live patient timeline.');
      }
    } catch (err) {
      console.error('Failed to query saved timeline:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
      setSavedTimelineError(`Database Query Error: ${detail}`);
    } finally {
      setIsFetchingSavedTimeline(false);
    }
  }, []);

  // Select a patient from the patient selector
  const selectPatient = useCallback((patient) => {
    if (!patient) return;
    setSelectedPatient(patient);
    setSelectedDate(''); // Reset active date so it dynamically defaults to the new patient's actual latest date
    setAnalysisData(null); // Clear previous in-memory OCR report
    fetchSavedTimeline(patient.patient_id);
  }, [fetchSavedTimeline]);

  // Check health, load metrics, samples, and patients on mount
  useEffect(() => {
    let isMounted = true;

    // 1. Health check
    reportAnalyzerApi.checkHealth().then((res) => {
      if (isMounted) {
        setBackendStatus(res && res.status === 'healthy' ? 'online' : 'offline');
      }
    });

    // 2. Dashboard metrics
    reportAnalyzerApi.getDashboardMetrics().then((res) => {
      if (isMounted && res.data && res.data.success) {
        setMetrics(res.data.data);
      }
    }).catch(() => {
      // Default fallback
    });

    // 3. Test samples
    reportAnalyzerApi.getSamples().then((res) => {
      if (isMounted && res.data && res.data.success) {
        setSamples(res.data.data || []);
      }
    }).catch(() => {
      if (isMounted) setSamples([]);
    });

    // 4. Patients list from Mst_Patients
    reportAnalyzerApi.getPatients().then((res) => {
      if (isMounted && res.data && res.data.success) {
        const patientList = res.data.data || [];
        setPatients(patientList);

        // Auto-select Patient 8 (Rohan Sharma) or Patient 9 (Rahul Sharma)
        if (patientList.length > 0) {
          const defaultPatient =
            patientList.find((p) => p.patient_id === 8 || (p.patient_name || '').toLowerCase().includes('rohan')) ||
            patientList.find((p) => p.patient_id === 9 || (p.patient_name || '').toLowerCase().includes('rahul')) ||
            patientList[0];
          setSelectedPatient(defaultPatient);
          fetchSavedTimeline(defaultPatient.patient_id);
        }
      }
    }).catch((err) => {
      console.error('Failed to load registered patients:', err);
      if (isMounted) setPatients([]);
    }).finally(() => {
      if (isMounted) setIsLoadingPatients(false);
    });

    return () => {
      isMounted = false;
    };
  }, [fetchSavedTimeline]);

  // Distinct available report dates for the selected patient
  const availableDates = useMemo(() => {
    const dates = new Set();
    if (analysisData?.report_date) {
      dates.add(analysisData.report_date);
    }
    if (savedTimelineData?.timeline) {
      savedTimelineData.timeline.forEach((item) => {
        if (item.report_date) {
          dates.add(String(item.report_date));
        }
      });
    }
    const arr = Array.from(dates);
    // Sort descending (latest date first)
    arr.sort((a, b) => new Date(b) - new Date(a));
    return arr;
  }, [analysisData, savedTimelineData]);

  // Derived effective date without cascading renders
  const activeDate = useMemo(() => {
    if (selectedDate && availableDates.includes(selectedDate)) {
      return selectedDate;
    }
    return availableDates.length > 0 ? availableDates[0] : '';
  }, [selectedDate, availableDates]);

  // Consolidated Lab Results displayed in Center Panel
  const patientLabResults = useMemo(() => {
    if (analysisData && Array.isArray(analysisData.results) && analysisData.results.length > 0) {
      return analysisData.results;
    }

    if (savedTimelineData?.timeline && savedTimelineData.timeline.length > 0) {
      const timeline = savedTimelineData.timeline;
      const dateFiltered = activeDate
        ? timeline.filter((t) => String(t.report_date) === String(activeDate))
        : timeline;

      const items = dateFiltered.length > 0 ? dateFiltered : timeline;

      return items.map((t) => ({
        test_name: t.parameter_name,
        parameter_name: t.parameter_name,
        value: t.test_result,
        test_result: t.test_result,
        unit: t.unit || '',
        reference_range: t.reference_range || '',
        status: t.status || 'NORMAL',
        parameter_id: t.parameter_id,
        category: 'Biochemistry / Hematology',
      }));
    }

    return [];
  }, [analysisData, savedTimelineData, activeDate]);

  // Recent Reports List for the selected patient
  const recentReports = useMemo(() => {
    if (availableDates.length > 0) {
      return availableDates.map((dateStr, idx) => {
        const cleanName = `Lab_Report_${dateStr.replace(/[\s-]/g, '')}.pdf`;
        return {
          id: `rep-${idx}`,
          filename: cleanName,
          date: `${dateStr}, 11:24 AM`,
          status: 'Processed',
          dateStr: dateStr,
        };
      });
    }
    return [];
  }, [availableDates]);

  // Handle local file selection
  const handleFileSelect = useCallback((file) => {
    if (!file) return;

    const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!allowedExtensions.includes(ext)) {
      setError(`Invalid file format '${ext}'. Allowed formats: PDF, PNG, JPG, JPEG.`);
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError(`File size (${formatBytes(file.size)}) exceeds maximum allowed limit of 15 MB.`);
      return;
    }

    setError(null);
    setSelectedFile(file);
    setFileName(file.name);
    setFileSizeStr(formatBytes(file.size));
    setSelectedSample('');
    setAnalysisData(null);
    setUploadProgress(0);
    setUploadModalOpen(true);
  }, []);

  // Handle sample selection from backend
  const handleSampleSelect = useCallback(async (sampleName) => {
    if (!sampleName) {
      setSelectedSample('');
      return;
    }

    setSelectedSample(sampleName);
    setIsLoadingSample(true);
    setError(null);

    try {
      const response = await reportAnalyzerApi.fetchSampleBlob(sampleName);
      let mimeType = 'application/pdf';
      if (sampleName.endsWith('.png')) mimeType = 'image/png';
      else if (sampleName.endsWith('.jpg') || sampleName.endsWith('.jpeg')) mimeType = 'image/jpeg';

      const file = new File([response.data], sampleName, { type: mimeType });
      setSelectedFile(file);
      setFileName(file.name);
      setFileSizeStr(formatBytes(file.size));
      setAnalysisData(null);
      setUploadProgress(0);
    } catch (err) {
      console.error('Failed to load sample report:', err);
      setError(`Failed to load sample report: ${err.message || 'Network error'}`);
    } finally {
      setIsLoadingSample(false);
    }
  }, []);

  // Run Report Analysis (OCR + Safe Patient Matching + Timeline Sync)
  const handleAnalyze = useCallback(async () => {
    if (!selectedFile) {
      setError('Please select or upload a medical report first.');
      return;
    }

    setIsAnalyzing(true);
    setUploadProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (selectedPatient?.patient_id) {
      formData.append('patient_id', selectedPatient.patient_id);
    }

    try {
      const response = await reportAnalyzerApi.analyzeReport(formData, (progress) => {
        setUploadProgress(progress);
      });

      if (response.data && response.data.success) {
        const payload = response.data.data;
        setAnalysisData(payload);
        setActiveFilter('ALL');
        setSearchQuery('');

        const match = payload?.patient_match;
        if (match && match.matched && match.patient_id) {
          const matchedPatient = patients.find((p) => p.patient_id === match.patient_id);
          if (matchedPatient) {
            setSelectedPatient(matchedPatient);
          }
          fetchSavedTimeline(match.patient_id);
        }
      } else {
        setError(response.data?.message || 'Report analysis failed.');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
      setError(`Analysis Error: ${detail}`);
    } finally {
      setIsAnalyzing(false);
      setUploadProgress(100);
    }
  }, [selectedFile, selectedPatient, patients, fetchSavedTimeline]);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setFileName('');
    setFileSizeStr('');
    setAnalysisData(null);
    setError(null);
    setActiveFilter('ALL');
    setSearchQuery('');
    setSelectedSample('');
    setUploadProgress(0);
  }, []);

  // Open Parameter Trend Modal
  const openParameterGraph = useCallback((paramItem) => {
    if (!paramItem) return;
    const name = paramItem.test_name || paramItem.parameter_name;
    const val = paramItem.value || paramItem.test_result;
    const unit = paramItem.unit || '';
    const ref = paramItem.reference_range || '';
    const status = paramItem.status || 'NORMAL';
    const parameterId = paramItem.parameter_id || null;
    const reportDate = paramItem.report_date || activeDate || '';

    setGraphParameter({
      name,
      parameterId,
      currentValue: val,
      unit,
      referenceRange: ref,
      currentStatus: status,
      reportDate,
    });
    setGraphModalOpen(true);
  }, [activeDate]);

  const closeParameterGraph = useCallback(() => {
    setGraphModalOpen(false);
    setGraphParameter(null);
  }, []);

  // Open Timeline Modal for Patient
  const openPatientTimeline = useCallback(async (patientId) => {
    if (!patientId) return;

    setTimelineModalOpen(true);
    setTimelineLoading(true);
    setTimelineError(null);
    setTimelineData(null);

    try {
      const response = await reportAnalyzerApi.getPatientTimeline(patientId);
      if (response.data && response.data.success) {
        setTimelineData(response.data.data);
      } else {
        setTimelineError(response.data?.message || 'Failed to fetch patient timeline history.');
      }
    } catch (err) {
      console.error('Failed to fetch patient timeline:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
      setTimelineError(`Timeline Fetch Error: ${detail}`);
    } finally {
      setTimelineLoading(false);
    }
  }, []);

  const closePatientTimeline = useCallback(() => {
    setTimelineModalOpen(false);
    setTimelineData(null);
    setTimelineError(null);
  }, []);

  const filteredResults = useMemo(() => {
    const list = patientLabResults;
    if (!Array.isArray(list) || list.length === 0) return [];

    return list.filter((item) => {
      const name = item.test_name || item.parameter_name || '';
      const status = item.status || 'NORMAL';

      if (activeFilter === 'NORMAL' && status !== 'NORMAL') return false;
      if (activeFilter === 'HIGH' && status !== 'HIGH') return false;
      if (activeFilter === 'LOW' && status !== 'LOW') return false;
      if (activeFilter === 'NEEDS REVIEW' && status !== 'NEEDS REVIEW') return false;

      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        const nameMatch = name.toLowerCase().includes(query);
        const valMatch = String(item.value || item.test_result || '').toLowerCase().includes(query);
        return nameMatch || valMatch;
      }

      return true;
    });
  }, [patientLabResults, activeFilter, searchQuery]);

  return {
    selectedFile,
    fileName,
    fileSizeStr,
    isAnalyzing,
    uploadProgress,
    analysisData,
    backendStatus,
    error,
    activeFilter,
    searchQuery,
    samples,
    selectedSample,
    isLoadingSample,
    patients,
    selectedPatient,
    isLoadingPatients,
    metrics,
    activeCenterTab,
    setActiveCenterTab,
    selectedDate: activeDate,
    setSelectedDate,
    availableDates,
    patientLabResults,
    recentReports,
    savedTimelineData,
    isFetchingSavedTimeline,
    savedTimelineError,
    fetchSavedTimeline,
    graphModalOpen,
    graphParameter,
    openParameterGraph,
    closeParameterGraph,
    uploadModalOpen,
    setUploadModalOpen,
    timelineModalOpen,
    timelineData,
    timelineLoading,
    timelineError,
    filteredResults,
    setActiveFilter,
    setSearchQuery,
    selectPatient,
    handleFileSelect,
    handleSampleSelect,
    handleAnalyze,
    handleReset,
    openPatientTimeline,
    closePatientTimeline,
  };
};

/* =========================================================================
   4. DASHBOARD METRICS CARDS
   ========================================================================= */
const DashboardMetricsCards = ({ metrics = null }) => {
  const hasData = metrics !== null && metrics !== undefined;

  const totalPatients = hasData && typeof metrics.total_patients === 'number' 
    ? metrics.total_patients.toLocaleString() 
    : '—';
  const totalReportsNum = hasData && typeof metrics.total_reports === 'number' ? metrics.total_reports : 0;
  const abnormalReportsNum = hasData && typeof metrics.abnormal_reports === 'number' ? metrics.abnormal_reports : 0;
  const processedReportsNum = hasData && typeof metrics.processed_reports === 'number' ? metrics.processed_reports : totalReportsNum;

  const totalReports = hasData && typeof metrics.total_reports === 'number'
    ? metrics.total_reports.toLocaleString()
    : '—';
  const abnormalReports = hasData && typeof metrics.abnormal_reports === 'number'
    ? metrics.abnormal_reports.toLocaleString()
    : '—';
  const processedReports = hasData && typeof metrics.processed_reports === 'number'
    ? metrics.processed_reports.toLocaleString()
    : '—';

  const patientsTrend = metrics?.patients_trend || '+12% this month';
  const reportsTrend = metrics?.reports_trend || '+8%';
  const abnormalPercent = metrics?.abnormal_percent || (totalReportsNum > 0 
    ? `${((abnormalReportsNum / totalReportsNum) * 100).toFixed(1)}% of total` 
    : '0% of total');
  const processedPercent = metrics?.processed_percent || (totalReportsNum > 0 
    ? `${((processedReportsNum / totalReportsNum) * 100).toFixed(1)}%` 
    : '100%');

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 font-sans">
      {/* Card 1: Total Patients */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex items-center gap-4 hover:shadow-sm transition-shadow">
        <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
          <Users className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-500">Total Patients</p>
          <p className="text-2xl font-black text-slate-900 leading-tight mt-0.5">
            {totalPatients}
          </p>
          <div className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 mt-1">
            <TrendingUp className="w-3 h-3" />
            <span>{patientsTrend}</span>
          </div>
        </div>
      </div>

      {/* Card 2: Total Reports */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex items-center gap-4 hover:shadow-sm transition-shadow">
        <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
          <FileText className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-500">Total Reports</p>
          <p className="text-2xl font-black text-slate-900 leading-tight mt-0.5">
            {totalReports}
          </p>
          <div className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 mt-1">
            <TrendingUp className="w-3 h-3" />
            <span>{reportsTrend}</span>
          </div>
        </div>
      </div>

      {/* Card 3: Abnormal Reports */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex items-center gap-4 hover:shadow-sm transition-shadow">
        <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-500">Abnormal Reports</p>
          <p className="text-2xl font-black text-slate-900 leading-tight mt-0.5">
            {abnormalReports}
          </p>
          <p className="text-[11px] font-semibold text-rose-600 mt-1">
            {abnormalPercent}
          </p>
        </div>
      </div>

      {/* Card 4: Processed Reports */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex items-center gap-4 hover:shadow-sm transition-shadow">
        <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
          <CheckCircle className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-500">Processed Reports</p>
          <p className="text-2xl font-black text-slate-900 leading-tight mt-0.5">
            {processedReports}
          </p>
          <p className="text-[11px] font-semibold text-emerald-600 mt-1">
            {processedPercent}
          </p>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   5. PATIENT SELECTION & DEMOGRAPHICS SECTION
   ========================================================================= */
const PatientInfoSection = ({
  patients = [],
  selectedPatient = null,
  onSelectPatient,
  isLoading = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredPatients = useMemo(() => {
    if (!searchTerm.trim()) return patients;
    const q = searchTerm.toLowerCase().trim();
    return patients.filter((p) => {
      const name = (p.patient_name || '').toLowerCase();
      const hid = (p.health_id || '').toLowerCase();
      const pid = String(p.patient_id || '');
      const phone = (p.phone || '').toLowerCase();
      return name.includes(q) || hid.includes(q) || pid.includes(q) || phone.includes(q);
    });
  }, [patients, searchTerm]);

  const initials = selectedPatient?.patient_name ? getInitials(selectedPatient.patient_name) : '—';
  const age = calculateAge(selectedPatient?.dob);
  const displayId = selectedPatient?.health_id || (selectedPatient?.patient_id ? `HC-2026-GEN-${selectedPatient.patient_id}` : '—');
  const displayName = selectedPatient?.patient_name || 'Select a patient...';
  const displayGender = selectedPatient?.gender || '—';
  const rawPhone = selectedPatient?.phone || '';
  const displayPhone = rawPhone ? (rawPhone.startsWith('+') ? rawPhone : `+91 ${rawPhone}`) : '—';

  return (
    <div className="bg-white rounded-3xl border border-slate-200/90 p-3 sm:p-4 shadow-xs mb-6 font-sans">
      <div className="flex flex-col lg:flex-row lg:items-center gap-4 lg:gap-6 justify-between">
        
        {/* Left Side: Embedded 'Select Patient' Card */}
        <div 
          className="bg-[#f0f6ff]/70 border border-blue-100/80 rounded-2xl p-3 sm:p-3.5 w-full lg:w-[350px] shrink-0" 
          ref={dropdownRef}
        >
          <div className="flex items-center gap-2 mb-2">
            <UserCheck className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-bold text-slate-900">Select Patient</span>
          </div>

          <div className="relative">
            <div
              onClick={() => setIsOpen(!isOpen)}
              className="w-full bg-white border border-slate-200 hover:border-blue-400 rounded-xl px-3 py-2 flex items-center justify-between gap-2 shadow-2xs cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className={`text-xs font-medium truncate ${selectedPatient ? 'text-slate-800 font-semibold' : 'text-slate-400'}`}>
                  {selectedPatient ? `${displayName} (${displayId})` : 'Search by Name, Patient ID, Health ID or Phone...'}
                </span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-blue-600 transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
            </div>

            {isOpen && (
              <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-72 flex flex-col overflow-hidden animate-slide-up">
                <div className="p-2.5 border-b border-slate-100 bg-slate-50/70">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      autoFocus
                      placeholder="Type name, ID, or phone to search..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-8 pr-7 py-1.5 text-xs bg-white border border-slate-200 rounded-lg outline-none focus:border-blue-500 text-slate-800"
                    />
                    {searchTerm && (
                      <button
                        onClick={() => setSearchTerm('')}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="overflow-y-auto divide-y divide-slate-100 py-1">
                  {isLoading ? (
                    <div className="py-6 text-center text-xs text-slate-400">
                      Loading registered patients...
                    </div>
                  ) : filteredPatients.length > 0 ? (
                    filteredPatients.map((p) => {
                      const isSelected = selectedPatient?.patient_id === p.patient_id;
                      const pInitials = getInitials(p.patient_name);
                      const pAge = calculateAge(p.dob);
                      return (
                        <button
                          key={p.patient_id}
                          type="button"
                          onClick={() => {
                            if (onSelectPatient) {
                              onSelectPatient(p);
                            }
                            setIsOpen(false);
                            setSearchTerm('');
                          }}
                          className={`w-full text-left px-3.5 py-2.5 flex items-center justify-between text-xs hover:bg-blue-50/60 transition-colors cursor-pointer ${
                            isSelected ? 'bg-blue-50/80 font-bold' : ''
                          }`}
                        >
                          <div className="flex items-center gap-2.5 truncate">
                            <div className="w-7 h-7 rounded-lg bg-blue-100 text-blue-800 font-bold text-[10px] flex items-center justify-center shrink-0">
                              {pInitials}
                            </div>
                            <div className="truncate">
                              <p className="font-bold text-slate-900 truncate">
                                {p.patient_name}{' '}
                                <span className="font-normal text-slate-400 text-[11px]">
                                  ({p.health_id || `ID: ${p.patient_id}`})
                                </span>
                              </p>
                              <p className="text-[10px] text-slate-500 font-medium">
                                {pAge} Y • {p.gender} • {p.phone || 'No phone'}
                              </p>
                            </div>
                          </div>
                          {isSelected && <Check className="w-4 h-4 text-blue-600 shrink-0" />}
                        </button>
                      );
                    })
                  ) : (
                    <div className="py-6 text-center text-xs text-slate-400">
                      No matching patients found.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="hidden lg:block w-px h-14 bg-slate-200/80 self-center" />

        {/* Right Section: Patient Demographics */}
        <div className="flex flex-wrap items-center gap-4 sm:gap-6 lg:gap-7 flex-1 justify-between lg:justify-start">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-full p-0.5 border-2 border-blue-200/80 bg-blue-50/60 flex items-center justify-center shrink-0 shadow-2xs">
              <div className="w-full h-full rounded-full bg-blue-100/70 text-blue-700 font-extrabold text-sm flex items-center justify-center">
                {initials}
              </div>
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-900 leading-tight">
                {displayName}
              </h3>
              <div className="mt-1 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-blue-50/90 border border-blue-200/70 text-xs font-semibold text-blue-700">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                <span>Health ID: {displayId}</span>
              </div>
            </div>
          </div>

          <div className="hidden lg:block w-px h-10 bg-slate-200/70" />

          {/* Age Block */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-50/80 border border-blue-100/60 text-blue-600 flex items-center justify-center shrink-0">
              <Calendar className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium leading-none">Age</p>
              <p className="text-xs font-bold text-slate-900 mt-0.5 leading-tight">{age} Years</p>
            </div>
          </div>

          <div className="hidden lg:block w-px h-10 bg-slate-200/70" />

          {/* Gender Block */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-50/80 border border-blue-100/60 text-blue-600 flex items-center justify-center shrink-0">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium leading-none">Gender</p>
              <p className="text-xs font-bold text-slate-900 mt-0.5 leading-tight">{displayGender}</p>
            </div>
          </div>

          <div className="hidden lg:block w-px h-10 bg-slate-200/70" />

          {/* Phone Block */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-50/80 border border-blue-100/60 text-blue-600 flex items-center justify-center shrink-0">
              <Phone className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium leading-none">Phone</p>
              <p className="text-xs font-bold text-slate-900 mt-0.5 leading-tight">{displayPhone}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   6. PATIENT ANALYSIS CENTER PANEL (4 TABS)
   ========================================================================= */
const PatientAnalysisCenterPanel = ({
  patient = null,
  activeTab = 'lab_results',
  onTabChange,
  availableDates = [],
  selectedDate = '',
  onDateChange,
  results = [],
  timelineRecords = [],
  onParameterClick,
  isLoading = false,
  selectedFile = null,
  analysisData: _analysisData = null,
}) => {
  const [selectedParamChips, setSelectedParamChips] = useState([]);
  const [prevPatientId, setPrevPatientId] = useState(patient?.patient_id);
  const [isParamDropdownOpen, setIsParamDropdownOpen] = useState(false);
  const [paramSearchText, setParamSearchText] = useState('');
  const paramDropdownRef = useRef(null);

  if (patient?.patient_id !== prevPatientId) {
    setPrevPatientId(patient?.patient_id);
    setSelectedParamChips([]);
  }

  useEffect(() => {
    function handleClickOutside(event) {
      if (paramDropdownRef.current && !paramDropdownRef.current.contains(event.target)) {
        setIsParamDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const allAvailableParamNames = useMemo(() => {
    const set = new Set();
    results.forEach((r) => {
      const name = r.test_name || r.parameter_name;
      if (name) set.add(name);
    });
    timelineRecords.forEach((t) => {
      if (t.parameter_name) set.add(t.parameter_name);
    });
    return Array.from(set);
  }, [results, timelineRecords]);

  const handleRemoveChip = (paramName) => {
    setSelectedParamChips((prev) => prev.filter((p) => p !== paramName));
  };

  const handleToggleChip = (paramName) => {
    setSelectedParamChips((prev) =>
      prev.includes(paramName) ? prev.filter((p) => p !== paramName) : [...prev, paramName]
    );
  };

  const handleSelectAllParams = () => {
    setSelectedParamChips(allAvailableParamNames);
  };

  const handleClearAllParams = () => {
    setSelectedParamChips([]);
  };

  const filteredDropdownParams = useMemo(() => {
    if (!paramSearchText.trim()) return allAvailableParamNames;
    const q = paramSearchText.toLowerCase().trim();
    return allAvailableParamNames.filter((p) => p.toLowerCase().includes(q));
  }, [allAvailableParamNames, paramSearchText]);

  const displayedResults = useMemo(() => {
    if (!results || results.length === 0) return [];
    if (selectedParamChips.length === 0) return results;

    const matching = results.filter((item) => {
      const name = item.test_name || item.parameter_name || '';
      return selectedParamChips.some((chip) => {
        const c = chip.toLowerCase();
        const n = name.toLowerCase();
        return n === c || n.includes(c) || c.includes(n);
      });
    });

    return matching.length > 0 ? matching : results;
  }, [results, selectedParamChips]);

  const getStatusBadge = (status) => {
    const s = (status || 'NORMAL').toUpperCase();
    if (s === 'HIGH') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
          High
        </span>
      );
    }
    if (s === 'LOW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
          Low
        </span>
      );
    }
    if (s === 'NEEDS REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
          Review
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
        Normal
      </span>
    );
  };

  const getValueColor = (status) => {
    const s = (status || 'NORMAL').toUpperCase();
    if (s === 'HIGH') return 'text-rose-600 font-bold';
    if (s === 'LOW') return 'text-blue-600 font-bold';
    return 'text-blue-800 font-bold';
  };

  const handleExportCSV = () => {
    if (!displayedResults || displayedResults.length === 0) return;
    const pName = patient?.patient_name || 'Patient';
    const rDate = selectedDate || 'Current';
    const headers = ['Parameter', 'Result', 'Unit', 'Reference Range', 'Status', 'Report Date', 'Patient Name'];
    const rows = displayedResults.map((r) => [
      `"${r.test_name || r.parameter_name}"`,
      `"${r.value || r.test_result}"`,
      `"${r.unit || ''}"`,
      `"${r.reference_range || ''}"`,
      `"${r.status || 'NORMAL'}"`,
      `"${rDate}"`,
      `"${pName}"`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Lab_Results_${pName.replace(/\s+/g, '_')}_${rDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const reportSessions = useMemo(() => {
    if (!timelineRecords || timelineRecords.length === 0) return [];
    const dateMap = {};
    timelineRecords.forEach((item) => {
      const d = item.report_date || 'Unknown Date';
      if (!dateMap[d]) {
        dateMap[d] = {
          date: d,
          parameters: [],
          abnormalCount: 0,
        };
      }
      dateMap[d].parameters.push(item);
      const st = (item.status || 'NORMAL').toUpperCase();
      if (st === 'HIGH' || st === 'LOW') {
        dateMap[d].abnormalCount += 1;
      }
    });

    return Object.values(dateMap).sort((a, b) => new Date(b.date) - new Date(a.date));
  }, [timelineRecords]);

  const analysisStats = useMemo(() => {
    const items = displayedResults.length > 0 ? displayedResults : timelineRecords;
    let normal = 0;
    let high = 0;
    let low = 0;
    let review = 0;

    items.forEach((item) => {
      const st = (item.status || 'NORMAL').toUpperCase();
      if (st === 'HIGH') high += 1;
      else if (st === 'LOW') low += 1;
      else if (st === 'NEEDS REVIEW') review += 1;
      else normal += 1;
    });

    const total = items.length;
    return {
      total,
      normal,
      high,
      low,
      review,
      abnormal: high + low + review,
    };
  }, [displayedResults, timelineRecords]);

  return (
    <div className="space-y-6">
      {/* 1. Four Navigation Tabs Bar */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => onTabChange && onTabChange('lab_results')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
            activeTab === 'lab_results'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <FlaskConical className="w-3.5 h-3.5" />
          <span>Result Timeline</span>
        </button>

        <button
          onClick={() => onTabChange && onTabChange('documents')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
            activeTab === 'documents'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Documents</span>
        </button>

        <button
          onClick={() => onTabChange && onTabChange('history')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
            activeTab === 'history'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Report History</span>
        </button>

        <button
          onClick={() => onTabChange && onTabChange('analysis')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
            activeTab === 'analysis'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Analysis</span>
        </button>
      </div>

      {/* 2. TAB 1: LAB RESULTS */}
      {activeTab === 'lab_results' && (
        <div className="space-y-6">
          {/* Choose Parameters Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Choose Parameters</h3>
            </div>

            <div className="relative" ref={paramDropdownRef}>
              <div
                onClick={() => setIsParamDropdownOpen(!isParamDropdownOpen)}
                className="w-full flex items-center justify-between gap-3 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-500 cursor-pointer hover:border-slate-300 shadow-2xs transition-all"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Search className="w-4 h-4 text-slate-400 shrink-0" />
                  <span className="truncate">
                    Search and select parameters (e.g. Hemoglobin, Glucose, WBC, RBC, MCV, MCH...)
                  </span>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform shrink-0 ${isParamDropdownOpen ? 'rotate-180' : ''}`} />
              </div>

              {isParamDropdownOpen && (
                <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl z-30 p-4 max-h-80 flex flex-col animate-slide-up">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 gap-3">
                    <div className="relative flex-1">
                      <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        autoFocus
                        placeholder="Search parameter..."
                        value={paramSearchText}
                        onChange={(e) => setParamSearchText(e.target.value)}
                        className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none focus:bg-white focus:border-blue-500"
                      />
                    </div>
                    <div className="flex items-center gap-2 text-xs font-bold shrink-0">
                      <button
                        type="button"
                        onClick={handleSelectAllParams}
                        className="text-blue-600 hover:text-blue-800 cursor-pointer"
                      >
                        Select All
                      </button>
                      <span className="text-slate-300">•</span>
                      <button
                        type="button"
                        onClick={handleClearAllParams}
                        className="text-slate-500 hover:text-slate-700 cursor-pointer"
                      >
                        Clear All
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 py-3 overflow-y-auto">
                    {filteredDropdownParams.map((param) => {
                      const isChecked = selectedParamChips.includes(param);
                      return (
                        <button
                          key={param}
                          type="button"
                          onClick={() => handleToggleChip(param)}
                          className={`text-left px-3 py-2 rounded-lg text-xs font-semibold truncate transition-colors flex items-center justify-between gap-1 cursor-pointer ${
                            isChecked
                              ? 'bg-blue-50 text-blue-800 font-bold border border-blue-200'
                              : 'bg-slate-50 hover:bg-slate-100 text-slate-700'
                          }`}
                        >
                          <span className="truncate">{param}</span>
                          {isChecked && <Check className="w-3 h-3 text-blue-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              {selectedParamChips.length > 0 ? (
                <>
                  {selectedParamChips.map((chip) => (
                    <span
                      key={chip}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-blue-50 text-blue-800 border border-blue-200 text-xs font-bold shadow-2xs animate-fade-in"
                    >
                      <span>{chip}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveChip(chip)}
                        className="hover:text-blue-950 p-0.5 cursor-pointer"
                        title={`Remove ${chip}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  <button
                    type="button"
                    onClick={handleClearAllParams}
                    className="text-[11px] font-bold text-slate-400 hover:text-slate-600 px-2 py-1 cursor-pointer"
                  >
                    Clear filter ({selectedParamChips.length})
                  </button>
                </>
              ) : (
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 py-0.5">
                  <span className="text-[11px] font-medium italic">
                    Showing all {displayedResults.length} parameters from database. Filter by searching above or clicking quick chips:
                  </span>
                  <div className="flex items-center gap-1.5">
                    {allAvailableParamNames.slice(0, 4).map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => handleToggleChip(p)}
                        className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 bg-blue-50/70 hover:bg-blue-100/70 px-2 py-0.5 rounded-md cursor-pointer transition-colors"
                      >
                        + {p}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Lab Results Table Section */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Lab Results</h3>
                <span className="text-[11px] text-slate-400 font-medium hidden sm:inline">
                  (Click any row or parameter to open trend graph)
                </span>
              </div>

              <div className="flex items-center gap-3">
                {availableDates.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-xs font-semibold text-slate-500">Report Date:</span>
                    <select
                      value={selectedDate}
                      onChange={(e) => onDateChange && onDateChange(e.target.value)}
                      className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-bold text-blue-700 outline-none cursor-pointer shadow-2xs hover:border-slate-300"
                    >
                      {availableDates.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleExportCSV}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-bold text-slate-700 shadow-2xs transition-colors cursor-pointer"
                  title="Export results to CSV"
                >
                  <Download className="w-3.5 h-3.5 text-slate-500" />
                  <span>Export</span>
                </button>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold text-[11px] uppercase tracking-wider">
                    <tr>
                      <th className="px-5 py-3.5">PARAMETER</th>
                      <th className="px-5 py-3.5">RESULT</th>
                      <th className="px-5 py-3.5">UNIT</th>
                      <th className="px-5 py-3.5">REFERENCE RANGE</th>
                      <th className="px-5 py-3.5">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {isLoading ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-400">
                          <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                          <p>Loading patient parameters from MSSQL...</p>
                        </td>
                      </tr>
                    ) : displayedResults.length > 0 ? (
                      displayedResults.map((row, idx) => {
                        const paramName = row.test_name || row.parameter_name;
                        const resultVal = row.value || row.test_result;

                        return (
                          <tr
                            key={`${paramName}-${idx}`}
                            onClick={() => onParameterClick && onParameterClick(row)}
                            className="hover:bg-blue-50/50 cursor-pointer transition-colors group"
                            title="Click to view chronological parameter graph"
                          >
                            <td className="px-5 py-3.5">
                              <div className="flex items-center gap-2">
                                <TrendingUp className="w-3.5 h-3.5 text-blue-600 shrink-0 group-hover:scale-110 transition-transform" />
                                <span className="font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
                                  {paramName}
                                </span>
                              </div>
                            </td>

                            <td className="px-5 py-3.5">
                              <span className={`text-sm ${getValueColor(row.status)}`}>
                                {resultVal}
                              </span>
                            </td>

                            <td className="px-5 py-3.5 font-medium text-slate-500">
                              {row.unit || '—'}
                            </td>

                            <td className="px-5 py-3.5 font-medium text-slate-600">
                              {row.reference_range || 'Standard'}
                            </td>

                            <td className="px-5 py-3.5">
                              {getStatusBadge(row.status)}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-400">
                          <FlaskConical className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                          <p className="font-semibold text-slate-600">No Parameters Found for this Date</p>
                          <p className="text-[11px] mt-0.5 text-slate-400">
                            Select a different report date or click "+ Upload Report" to analyze a new file.
                          </p>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. TAB 2: DOCUMENTS */}
      {activeTab === 'documents' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <span>Diagnostic Documents & Laboratory Reports</span>
            </h3>
            <span className="text-xs text-slate-500 font-medium">
              Patient: <strong>{patient?.patient_name}</strong>
            </span>
          </div>

          {availableDates.length === 0 && !selectedFile ? (
            <div className="py-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">
              <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="font-semibold text-slate-600">No Documents Found</p>
              <p className="text-[11px] mt-0.5 text-slate-400">
                No diagnostic documents or laboratory reports recorded in database for {patient?.patient_name || 'this patient'}.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {selectedFile && (
                <div className="p-4 bg-white border border-blue-200 rounded-2xl shadow-xs space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate">
                        {selectedFile.name}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Uploaded File • {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <span className="inline-block mt-1 text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Current Active Report
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {availableDates.map((dateStr, i) => (
                <div key={i} className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs space-y-3 hover:border-slate-300 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate">
                        Lab_Report_{dateStr.replace(/[\s-]/g, '')}.pdf
                      </p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Verified Laboratory PDF • Date: {dateStr}
                      </p>
                      <span className="inline-block mt-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        MSSQL Timeline Record
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-slate-100 text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        if (onDateChange) onDateChange(dateStr);
                        if (onTabChange) onTabChange('lab_results');
                      }}
                      className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold transition-colors cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5 text-slate-500" />
                      <span>View in Table</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleExportCSV}
                      className="flex items-center justify-center p-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
                      title="Export report CSV"
                    >
                      <FileDown className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 4. TAB 3: REPORT HISTORY */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span>Historical Laboratory Report Sessions</span>
            </h3>
            <span className="text-xs text-slate-500">
              Total Recorded Sessions: <strong>{reportSessions.length}</strong>
            </span>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5">REPORT DATE</th>
                  <th className="px-5 py-3.5">DOCUMENT</th>
                  <th className="px-5 py-3.5">TOTAL TESTS</th>
                  <th className="px-5 py-3.5">ABNORMAL FINDINGS</th>
                  <th className="px-5 py-3.5">STATUS</th>
                  <th className="px-5 py-3.5 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reportSessions.length > 0 ? (
                  reportSessions.map((session, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-5 py-3.5 font-bold text-slate-900">
                        {session.date}
                      </td>
                      <td className="px-5 py-3.5 font-medium text-slate-600 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-rose-500" />
                        <span>Lab_Report_{session.date.replace(/[\s-]/g, '')}.pdf</span>
                      </td>
                      <td className="px-5 py-3.5 font-bold text-blue-700">
                        {session.parameters.length} Parameters
                      </td>
                      <td className="px-5 py-3.5 font-bold text-rose-600">
                        {session.abnormalCount > 0 ? `${session.abnormalCount} Out of Range` : 'None (All Normal)'}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          session.abnormalCount > 0
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}>
                          {session.abnormalCount > 0 ? 'Abnormal Findings' : 'Normal Profile'}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            if (onDateChange) onDateChange(session.date);
                            if (onTabChange) onTabChange('lab_results');
                          }}
                          className="px-3 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-bold text-xs transition-colors cursor-pointer"
                        >
                          View Results
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No previous report sessions found in database for this patient.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. TAB 4: ANALYSIS */}
      {activeTab === 'analysis' && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs">
              <p className="text-[11px] font-bold text-slate-500 uppercase">Total Tests Analyzed</p>
              <p className="text-2xl font-black text-slate-900 mt-1">{analysisStats.total}</p>
            </div>
            <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-2xl shadow-xs">
              <p className="text-[11px] font-bold text-emerald-700 uppercase">Normal Parameters</p>
              <p className="text-2xl font-black text-emerald-800 mt-1">{analysisStats.normal}</p>
            </div>
            <div className="p-4 bg-rose-50/50 border border-rose-200 rounded-2xl shadow-xs">
              <p className="text-[11px] font-bold text-rose-700 uppercase">High Values</p>
              <p className="text-2xl font-black text-rose-800 mt-1">{analysisStats.high}</p>
            </div>
            <div className="p-4 bg-blue-50/50 border border-blue-200 rounded-2xl shadow-xs">
              <p className="text-[11px] font-bold text-blue-700 uppercase">Low Values</p>
              <p className="text-2xl font-black text-blue-800 mt-1">{analysisStats.low}</p>
            </div>
          </div>

          {analysisStats.total > 0 && (
            <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs space-y-2">
              <div className="flex justify-between text-xs font-bold text-slate-700">
                <span>Parameter Clinical Distribution</span>
                <span>
                  {((analysisStats.normal / analysisStats.total) * 100).toFixed(0)}% Normal Rate
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden flex">
                <div
                  className="bg-emerald-500 h-3"
                  style={{ width: `${(analysisStats.normal / analysisStats.total) * 100}%` }}
                  title={`Normal: ${analysisStats.normal}`}
                />
                <div
                  className="bg-rose-500 h-3"
                  style={{ width: `${(analysisStats.high / analysisStats.total) * 100}%` }}
                  title={`High: ${analysisStats.high}`}
                />
                <div
                  className="bg-blue-500 h-3"
                  style={{ width: `${(analysisStats.low / analysisStats.total) * 100}%` }}
                  title={`Low: ${analysisStats.low}`}
                />
              </div>
              <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-1">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>Normal ({analysisStats.normal})</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                  <span>High ({analysisStats.high})</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                  <span>Low ({analysisStats.low})</span>
                </span>
              </div>
            </div>
          )}

          {analysisStats.abnormal > 0 && (
            <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs space-y-3">
              <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>Out-of-Range Parameters (Requires Clinical Review)</span>
              </h4>

              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold text-[10px] uppercase">
                    <tr>
                      <th className="px-4 py-2.5">Parameter</th>
                      <th className="px-4 py-2.5">Observed Result</th>
                      <th className="px-4 py-2.5">Reference Interval</th>
                      <th className="px-4 py-2.5">Deviation</th>
                      <th className="px-4 py-2.5 text-right">Trend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {displayedResults
                      .filter((r) => (r.status || '').toUpperCase() === 'HIGH' || (r.status || '').toUpperCase() === 'LOW')
                      .map((row, idx) => (
                        <tr
                          key={idx}
                          onClick={() => onParameterClick && onParameterClick(row)}
                          className="hover:bg-slate-50 cursor-pointer"
                        >
                          <td className="px-4 py-2.5 font-bold text-slate-900">
                            {row.test_name || row.parameter_name}
                          </td>
                          <td className="px-4 py-2.5 font-black text-rose-600">
                            {row.value || row.test_result} {row.unit}
                          </td>
                          <td className="px-4 py-2.5 text-slate-500 font-medium">
                            {row.reference_range} {row.unit}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                              {(row.status || 'HIGH').toUpperCase()}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right font-bold text-blue-600 hover:underline">
                            View Graph →
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-start gap-3 text-xs text-slate-600">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong>Automated Laboratory Observation Note:</strong> The above statistical distributions and reference comparisons are deterministic observations generated from OCR test extraction. These automated observations are provided for clinical reference only and do not constitute an autonomous medical diagnosis. Please correlate with clinical patient symptoms and physician consultation.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

/* =========================================================================
   7. UPLOAD & OCR ANALYSIS MODAL
   ========================================================================= */
const UploadReportModal = ({
  isOpen = false,
  onClose,
  selectedFile = null,
  fileName = '',
  fileSizeStr = '',
  isAnalyzing = false,
  uploadProgress = 0,
  analysisData = null,
  error = null,
  onFileSelect,
  onAnalyze,
  timelineSyncSuccess = false,
}) => {
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleOpenPicker = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const handleNativeChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const patientMatch = analysisData?.patient_match;
  const isMatched = patientMatch?.matched;
  const extractedCount = analysisData?.results?.length || 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
      <div 
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {analysisData ? 'Medical Report Analysis Complete' : 'Upload & Analyze Medical Report'}
              </h3>
              <p className="text-xs text-slate-500">
                {analysisData ? 'Deterministic OCR extraction and patient timeline integration' : 'Select a laboratory PDF or image (Max 15 MB)'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-slate-200 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleNativeChange}
            className="hidden"
          />

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {selectedFile ? (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between gap-4">
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-slate-900 truncate">
                    {fileName}
                  </p>
                  <p className="text-[11px] text-slate-500 font-medium mt-0.5">
                    {fileSizeStr} • Verified Format
                  </p>
                </div>
              </div>

              {!isAnalyzing && (
                <button
                  type="button"
                  onClick={handleOpenPicker}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 transition-colors shrink-0 cursor-pointer"
                >
                  Change File
                </button>
              )}
            </div>
          ) : (
            <div
              onClick={handleOpenPicker}
              className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-2xl p-8 text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-blue-50/30"
            >
              <Upload className="w-10 h-10 text-blue-600 mx-auto mb-3" />
              <p className="text-sm font-bold text-slate-800">
                Click to browse or drop medical report
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Supports PDF, PNG, JPG, JPEG (Max 15 MB)
              </p>
            </div>
          )}

          {isAnalyzing && (
            <div className="space-y-3 py-2">
              <div className="flex justify-between text-xs font-bold text-slate-700">
                <span className="flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                  <span>Analyzing report with Deterministic OCR Engine...</span>
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400 text-center">
                Extracting clinical test names, numeric results, units, biological reference intervals & patient match...
              </p>
            </div>
          )}

          {analysisData && !isAnalyzing && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <p className="text-[10px] uppercase font-bold text-slate-400">Extracted Tests</p>
                  <p className="text-lg font-black text-slate-900 mt-0.5">{extractedCount}</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <p className="text-[10px] uppercase font-bold text-slate-400">Report Date</p>
                  {analysisData.report_date && !analysisData.requires_date_verification ? (
                    <p className="text-xs font-bold text-slate-800 mt-1">{analysisData.report_date}</p>
                  ) : (
                    <span 
                      className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 mt-1"
                      title="OCR could not confidently identify report date. Flagged for manual clinical verification. Upload timestamp was NOT used."
                    >
                      ⚠️ Unverified (Flagged)
                    </span>
                  )}
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <p className="text-[10px] uppercase font-bold text-slate-400">Report Patient</p>
                  <p className="text-xs font-bold text-slate-800 mt-1 truncate">{analysisData.patient_name || 'Anonymous'}</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <p className="text-[10px] uppercase font-bold text-slate-400">Patient Match</p>
                  <div className="mt-1">
                    {isMatched ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        <UserCheck className="w-3 h-3" />
                        <span>Matched</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        <span>New / Manual</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {isMatched && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>
                      Matched registered patient: <strong>{patientMatch.patient_name}</strong> (ID: {patientMatch.patient_id})
                    </span>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/60 px-2 py-0.5 rounded">
                    Confidence: {(patientMatch.match_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}

              {timelineSyncSuccess && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-center gap-2">
                  <Database className="w-4 h-4 text-blue-600 shrink-0" />
                  <span>Extracted parameters safely recorded to patient health timeline in MSSQL database.</span>
                </div>
              )}

              <div className="border border-slate-200 rounded-xl overflow-hidden max-h-48 overflow-y-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold text-[10px] uppercase">
                    <tr>
                      <th className="px-3 py-2">Parameter</th>
                      <th className="px-3 py-2">Result</th>
                      <th className="px-3 py-2">Unit</th>
                      <th className="px-3 py-2">Reference Range</th>
                      <th className="px-3 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {analysisData.results?.map((res, i) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="px-3 py-2 font-bold text-slate-900">{res.test_name}</td>
                        <td className="px-3 py-2 font-black text-slate-800">{res.value}</td>
                        <td className="px-3 py-2 text-slate-500">{res.unit || '—'}</td>
                        <td className="px-3 py-2 text-slate-500">{res.reference_range || 'Standard'}</td>
                        <td className="px-3 py-2">
                          <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            res.status === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                            res.status === 'LOW' ? 'bg-blue-100 text-blue-800' :
                            'bg-emerald-100 text-emerald-800'
                          }`}>
                            {res.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-slate-100 bg-slate-50/70 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Deterministic Rule-based OCR & MSSQL</span>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={onClose}>
              {analysisData ? 'Done' : 'Cancel'}
            </Button>

            {!analysisData && selectedFile && (
              <Button
                variant="primary"
                size="sm"
                onClick={onAnalyze}
                disabled={isAnalyzing}
                className="flex items-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Report Analyzer</span>
                  </>
                )}
              </Button>
            )}

            {analysisData && (
              <Button
                variant="primary"
                size="sm"
                onClick={onClose}
                className="flex items-center gap-1.5"
              >
                <span>View in Dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   8. HISTORICAL TIMELINE MODAL (3-Table SQL JOIN Audit View)
   ========================================================================= */
const HistoricalTimelineModal = ({
  isOpen = false,
  onClose,
  timelineData = null,
  loading = false,
  error = null,
}) => {
  const [timelineSearch, setTimelineSearch] = useState('');

  const patient = timelineData?.patient || {};
  const timelineList = timelineData?.timeline;

  const filteredRecords = useMemo(() => {
    const records = timelineList || [];
    if (!timelineSearch.trim()) return records;
    const q = timelineSearch.trim().toLowerCase();
    return records.filter((item) => {
      const pName = (item.parameter_name || '').toLowerCase();
      const val = (item.test_result || '').toLowerCase();
      const dateStr = (item.report_date || '').toLowerCase();
      return pName.includes(q) || val.includes(q) || dateStr.includes(q);
    });
  }, [timelineList, timelineSearch]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
      <div
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center">
              <History className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">
                  Patient Health Timeline
                </h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
                  Verified 3-Table SQL JOIN
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Direct view from <code className="text-teal-700 font-mono text-[11px]">dbo.HC_Patient_Health_Timeline</code>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {patient && (
          <div className="px-5 py-3.5 bg-teal-50/60 border-b border-teal-100 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-teal-700" />
              <span className="font-bold text-slate-900 text-sm">
                {patient.patient_name || 'Patient'}
              </span>
              {patient.health_id && (
                <span className="font-mono text-teal-800 font-bold bg-white px-2 py-0.5 rounded border border-teal-200">
                  {patient.health_id}
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-4 text-slate-600">
              {patient.gender && (
                <span>Gender: <strong className="text-slate-800">{patient.gender}</strong></span>
              )}
              {patient.dob && (
                <span>DOB: <strong className="text-slate-800">{patient.dob}</strong></span>
              )}
              {patient.phone && (
                <span>Phone: <strong className="text-slate-800">{patient.phone}</strong></span>
              )}
              <span className="bg-teal-600 text-white font-bold px-2.5 py-0.5 rounded-full text-[11px]">
                {timelineData?.total_records || filteredRecords.length} Total Records
              </span>
            </div>
          </div>
        )}

        <div className="p-4 border-b border-slate-100 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search historical timeline parameters..."
              value={timelineSearch}
              onChange={(e) => setTimelineSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-teal-500 outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="text-center py-16">
              <div className="w-10 h-10 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-600">Querying Patient Health Timeline...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              <strong>Error loading timeline:</strong> {error}
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="text-center py-16">
              <FileSpreadsheet className="w-12 h-12 text-slate-300 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-700">No Timeline Records Found</h4>
              <p className="text-xs text-slate-400 mt-1">
                {timelineSearch ? 'No parameters matched your search.' : 'No previous lab recordings exist for this patient.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold text-[10px] uppercase">
                  <tr>
                    <th className="px-4 py-2.5">Report Date</th>
                    <th className="px-4 py-2.5">Clinical Parameter</th>
                    <th className="px-4 py-2.5">Recorded Value</th>
                    <th className="px-4 py-2.5">Saved On (UTC)</th>
                    <th className="px-4 py-2.5">Timeline ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredRecords.map((item) => (
                    <tr key={item.timeline_id} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <Calendar className="w-3.5 h-3.5 text-teal-600" />
                          <span>{item.report_date || 'N/A'}</span>
                        </div>
                      </td>

                      <td className="px-4 py-2.5">
                        <p className="text-sm font-bold text-slate-900">{item.parameter_name}</p>
                        <span className="text-[11px] text-slate-400 font-mono">
                          Param ID: {item.parameter_id}
                        </span>
                      </td>

                      <td className="px-4 py-2.5">
                        <span className="text-sm font-black text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-100">
                          {item.test_result}
                        </span>
                      </td>

                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1 text-xs text-slate-500">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            {item.saved_on ? new Date(item.saved_on).toLocaleString() : 'N/A'}
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-2.5">
                        <span className="text-xs font-mono text-slate-400">
                          #{item.timeline_id}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Database className="w-4 h-4 text-teal-600" />
            <span>MSSQL Connection Active • dbo.HC_Patient_Health_Timeline</span>
          </div>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   9. TOP-LEVEL MAIN REPORT ANALYZER MODULE COMPONENT
   ========================================================================= */
export const ReportAnalyzer = () => {
  const fileInputRef = useRef(null);

  const {
    selectedFile,
    fileName,
    fileSizeStr,
    isAnalyzing,
    uploadProgress,
    analysisData,
    backendStatus,
    error,
    patients,
    selectedPatient,
    isLoadingPatients,
    metrics,
    activeCenterTab,
    setActiveCenterTab,
    selectedDate,
    setSelectedDate,
    availableDates,
    patientLabResults,
    savedTimelineData,
    isFetchingSavedTimeline,
    graphModalOpen,
    graphParameter,
    openParameterGraph,
    closeParameterGraph,
    uploadModalOpen,
    setUploadModalOpen,
    timelineModalOpen,
    timelineData,
    timelineLoading,
    timelineError,
    closePatientTimeline,
    selectPatient,
    handleFileSelect,
    handleAnalyze,
  } = useReportAnalyzer();

  const handleUploadBtnClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const handleNativeFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const warnings = analysisData?.warnings || [];

  return (
    <div className="max-w-[1520px] mx-auto px-4 sm:px-6 py-5 font-sans">
      {/* Hidden File Picker Input (1-click trigger) */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf,.png,.jpg,.jpeg"
        onChange={handleNativeFileChange}
        className="hidden"
      />

      {/* 1. Breadcrumb Bar */}
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2">
        <span className="hover:text-slate-800 transition-colors cursor-pointer">Healthcare Connect</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
        <span className="hover:text-slate-800 transition-colors cursor-pointer">Patient Reports</span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-slate-900 font-bold">Report Analysis</span>
      </div>

      {/* 2. Top Header with Title, Subtitle and '+ Upload Report' Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Patient Report Analysis
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            View patient lab parameters, analyze results and manage reports
          </p>
        </div>

        <div>
          <button
            type="button"
            onClick={handleUploadBtnClick}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-xs rounded-xl shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Upload Report</span>
          </button>
        </div>
      </div>

      {/* Error & Warnings Banners */}
      {error && (
        <div className="mb-5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5 shadow-2xs animate-fade-in">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold">Notice: </span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="mb-5 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2 animate-fade-in">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>{warnings[0]}</span>
        </div>
      )}

      {/* 3. Top Metrics Row (Full Width) */}
      <DashboardMetricsCards metrics={metrics} />

      {/* 4. Patient Selection & Demographic Information */}
      <PatientInfoSection
        patients={patients}
        selectedPatient={selectedPatient}
        onSelectPatient={selectPatient}
        isLoading={isLoadingPatients}
      />

      {/* 5. Center Panel: 4 Functional Tabs & Content */}
      <PatientAnalysisCenterPanel
        patient={selectedPatient}
        activeTab={activeCenterTab}
        onTabChange={setActiveCenterTab}
        availableDates={availableDates}
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
        results={patientLabResults}
        timelineRecords={savedTimelineData?.timeline || []}
        onParameterClick={openParameterGraph}
        isLoading={isFetchingSavedTimeline}
        selectedFile={selectedFile}
        analysisData={analysisData}
      />

      {/* 6. Upload & OCR Analysis Modal */}
      <UploadReportModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        selectedFile={selectedFile}
        fileName={fileName}
        fileSizeStr={fileSizeStr}
        isAnalyzing={isAnalyzing}
        uploadProgress={uploadProgress}
        analysisData={analysisData}
        error={error}
        onFileSelect={handleFileSelect}
        onAnalyze={handleAnalyze}
      />

      {/* 7. Interactive Parameter Trend Graph Modal */}
      <ParameterTrendChart
        isOpen={graphModalOpen}
        onClose={closeParameterGraph}
        parameterName={graphParameter?.name || ''}
        parameterId={graphParameter?.parameterId || null}
        patient={selectedPatient}
        timelineRecords={savedTimelineData?.timeline || []}
        unit={graphParameter?.unit || ''}
        referenceRange={graphParameter?.referenceRange || ''}
        currentValue={graphParameter?.currentValue || ''}
        currentStatus={graphParameter?.currentStatus || ''}
        reportDate={graphParameter?.reportDate || selectedDate || ''}
      />

      {/* 8. Historical Timeline Modal */}
      <HistoricalTimelineModal
        isOpen={timelineModalOpen}
        onClose={closePatientTimeline}
        timelineData={timelineData}
        loading={timelineLoading}
        error={timelineError}
      />

      {/* Footer Info Ribbon */}
      <div className="mt-8 pt-4 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Healthcare Connect • Connected to MSSQL Database (HealthCare_connect)</span>
        </div>
        <div>
          <span>API Status: </span>
          <strong className={backendStatus === 'online' ? 'text-emerald-600' : 'text-rose-500'}>
            {backendStatus === 'online' ? 'Online' : 'Offline'}
          </strong>
        </div>
      </div>
    </div>
  );
};

export { ReportAnalyzer as ReportAnalyzerScreen };
export default ReportAnalyzer;
