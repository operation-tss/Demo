import React, { useState } from 'react';
import { 
  HeartPulse, 
  FileSearch, 
  FlaskConical, 
  Users, 
  Calendar, 
  Settings, 
  Database, 
  Menu, 
  X,
  Stethoscope,
  ChevronRight
} from 'lucide-react';
import ReportAnalyzer from './features/report-analyzer/ReportAnalyzer';

export default function App() {
  const [activeTab, setActiveTab] = useState('analyzer');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden text-slate-800">
      {/* Sidebar Navigation */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 flex flex-col transition-transform duration-200 ease-in-out md:static md:translate-x-0
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-md shadow-teal-700/20">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-tight text-slate-900 block leading-tight">
                Healthcare_Connect
              </span>
              <span className="text-[10px] font-bold text-teal-600 uppercase tracking-wider block">
                Diagnostic Engine
              </span>
            </div>
          </div>
          <button 
            className="md:hidden text-slate-400 hover:text-slate-600"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Diagnostic Modules
          </div>

          <button
            onClick={() => { setActiveTab('analyzer'); setMobileMenuOpen(false); }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
              activeTab === 'analyzer'
                ? 'bg-teal-50 text-teal-800 border border-teal-200/60 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <FileSearch className={`w-4 h-4 ${activeTab === 'analyzer' ? 'text-teal-600' : 'text-slate-400'}`} />
            <span className="flex-1 text-left">Report Analyzer</span>
            {activeTab === 'analyzer' && <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />}
          </button>

          <button
            onClick={() => { setActiveTab('lab_reports'); setMobileMenuOpen(false); }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
              activeTab === 'lab_reports'
                ? 'bg-teal-50 text-teal-800 border border-teal-200/60 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <FlaskConical className={`w-4 h-4 ${activeTab === 'lab_reports' ? 'text-teal-600' : 'text-slate-400'}`} />
            <span className="flex-1 text-left">Lab Reports</span>
          </button>

          <div className="pt-4 px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Clinical Operations
          </div>

          <button
            onClick={() => { setActiveTab('patients'); setMobileMenuOpen(false); }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
              activeTab === 'patients'
                ? 'bg-teal-50 text-teal-800 border border-teal-200/60 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Users className="w-4 h-4 text-slate-400" />
            <span className="flex-1 text-left">Patients Directory</span>
          </button>

          <button
            onClick={() => { setActiveTab('appointments'); setMobileMenuOpen(false); }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
              activeTab === 'appointments'
                ? 'bg-teal-50 text-teal-800 border border-teal-200/60 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="flex-1 text-left">Appointments</span>
          </button>

          <button
            onClick={() => { setActiveTab('settings'); setMobileMenuOpen(false); }}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer ${
              activeTab === 'settings'
                ? 'bg-teal-50 text-teal-800 border border-teal-200/60 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Settings className="w-4 h-4 text-slate-400" />
            <span className="flex-1 text-left">Configuration</span>
          </button>
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-800 font-black text-xs flex items-center justify-center">
              DR
            </div>
            <div className="text-xs overflow-hidden">
              <p className="font-bold text-slate-900 truncate">Clinical Lead</p>
              <p className="text-[10px] text-teal-700 font-semibold truncate">HealthCare_connect</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Mobile menu trigger for small screens */}
        <div className="md:hidden px-4 py-2.5 bg-white border-b border-slate-200 flex items-center justify-between shrink-0">
          <button
            className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 cursor-pointer"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="text-xs font-bold text-slate-800">Healthcare Connect</span>
          <div className="w-6" />
        </div>

        {/* Top Header Bar (Shown only for non-analyzer modules) */}
        {activeTab !== 'analyzer' && (
          <header className="h-16 bg-white border-b border-slate-200 px-4 md:px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                <span>Healthcare Connect</span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-900 font-bold capitalize">{activeTab}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3 text-xs">
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 font-semibold">
                <Database className="w-3.5 h-3.5 text-teal-600" />
                <span>MSSQL: HealthCare_connect</span>
              </div>
            </div>
          </header>
        )}

        {/* Content View */}
        <main className="flex-1 overflow-y-auto bg-slate-50">
          {activeTab === 'analyzer' && <ReportAnalyzer />}

          {activeTab === 'lab_reports' && (
            <div className="max-w-4xl mx-auto py-12 px-4 text-center">
              <FlaskConical className="w-12 h-12 text-teal-600 mx-auto mb-3" />
              <h3 className="text-lg font-bold text-slate-900">Lab Reports Repository</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
                To analyze lab reports or extract test parameters directly into the timeline, use the Medical Report Analyzer module.
              </p>
              <button
                onClick={() => setActiveTab('analyzer')}
                className="px-4 py-2 bg-teal-600 text-white font-bold text-xs rounded-xl shadow-sm hover:bg-teal-700 transition-colors cursor-pointer"
              >
                Go to Report Analyzer
              </button>
            </div>
          )}

          {activeTab !== 'analyzer' && activeTab !== 'lab_reports' && (
            <div className="max-w-4xl mx-auto py-12 px-4 text-center">
              <Stethoscope className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-lg font-bold text-slate-700 capitalize">{activeTab} Management</h3>
              <p className="text-xs text-slate-400 mt-1">
                This module is integrated in the parent Healthcare Connect system.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
