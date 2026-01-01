"use client"

import { useState, useEffect } from 'react';
import { FileText, Download, Search, Database, Loader2, CheckCircle, XCircle, Eye, MapPin, Home, Calendar, DollarSign, User, RefreshCw } from 'lucide-react';

interface DownloadedFile {
    doc_id: string;
    filename: string;
    size_bytes?: number;
    type?: string;
}

interface SearchResult {
    doc_id: string;
    doc_number: string;
    doc_type: string;
    record_date: string;
}

interface ExtractedData {
    document_type: string;
    property_address: string | null;
    parcel_number: string | null;
    legal_description: string | null;
    debtor_name: string | null;
    creditor_name: string | null;
    amount: string | null;
    recording_date: string | null;
    case_number: string | null;
    trustee_sale_date: string | null;
    summary: string | null;
}

interface SessionStatus {
    initialized: boolean;
    needs_captcha: boolean;
    ready: boolean;
    message: string;
}

const DOC_TYPES = [
    { id: 'lis', name: 'LIS PENDENS', desc: 'Pre-foreclosure notices' },
    { id: 'nots', name: 'NOTICE SALE', desc: 'Foreclosure sales' },
    { id: 'sub', name: 'SUBSTITUTION TRUSTEE', desc: 'Trustee changes' },
    { id: 'federal', name: 'FEDERAL LIEN', desc: 'IRS tax liens' },
    { id: 'city', name: 'CITY LIEN', desc: 'Municipal liens' },
    { id: 'mechanic', name: 'MECHANICS LIEN', desc: 'Contractor liens' },
    { id: 'judgment', name: 'JUDGMENT', desc: 'Court judgments' },
    { id: 'divorce', name: 'DISSOLUTION MARRIAGE', desc: 'Divorce records' },
];

export function RecorderDocuments() {
    const [downloads, setDownloads] = useState<DownloadedFile[]>([]);
    const [status, setStatus] = useState<SessionStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [extracting, setExtracting] = useState<string | null>(null);
    const [extractedData, setExtractedData] = useState<Record<string, ExtractedData>>({});

    // Search state
    const [selectedDocType, setSelectedDocType] = useState<string>('lis');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [searching, setSearching] = useState(false);
    const [downloading, setDownloading] = useState<string | null>(null);
    const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
    const [activeTab, setActiveTab] = useState<'downloads' | 'search'>('downloads');

    const API_BASE = 'http://127.0.0.1:8000/api/v1/recorder';

    useEffect(() => {
        fetchStatus();
        fetchDownloads();
    }, []);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/status`);
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
            } else {
                throw new Error(`Status request failed: ${res.status}`);
            }
        } catch (error) {
            console.error('Failed to fetch status:', error);
            setStatus({
                initialized: false,
                needs_captcha: false,
                ready: false,
                message: 'Backend connection failed. Check console for details.'
            });
        }
    };

    const fetchDownloads = async () => {
        try {
            const res = await fetch(`${API_BASE}/downloads`);
            if (res.ok) {
                const data = await res.json();
                // Deduplicate files by doc_id
                const uniqueFiles = Array.from(new Map((data.files || []).map((f: DownloadedFile) => [f.doc_id, f])).values());
                setDownloads(uniqueFiles as DownloadedFile[]);
            }
        } catch (error) {
            console.error('Failed to fetch downloads:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        setSearching(true);
        setSearchResults([]);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

        try {
            // Backend will auto-initialize browser session if needed
            const res = await fetch(`${API_BASE}/search/${selectedDocType}`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            if (!res.ok) {
                const error = await res.json();
                alert(error.detail || 'Search failed');
                return;
            }
            const data = await res.json();
            setSearchResults(data.results || []);
            // Refresh status after search (session may have been initialized)
            fetchStatus();
        } catch (error) {
            console.error('Search failed:', error);
            alert('Search failed. Please check if the backend is running.');
        } finally {
            setSearching(false);
        }
    };

    const toggleSelectAll = () => {
        if (selectedDocs.size === searchResults.length) {
            setSelectedDocs(new Set());
        } else {
            setSelectedDocs(new Set(searchResults.map(r => r.doc_id)));
        }
    };

    const toggleSelect = (docId: string) => {
        const newSelected = new Set(selectedDocs);
        if (newSelected.has(docId)) {
            newSelected.delete(docId);
        } else {
            newSelected.add(docId);
        }
        setSelectedDocs(newSelected);
    };

    const handleBulkDownload = async () => {
        if (selectedDocs.size === 0) return;

        const docsToDownload = Array.from(selectedDocs);
        // Sequential download to avoid race conditions
        for (const docId of docsToDownload) {
            await handleDownload(docId);
        }
        setSelectedDocs(new Set());
    };

    const handleDownload = async (docId: string) => {
        setDownloading(docId);
        try {
            const res = await fetch(`${API_BASE}/download/${docId}`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                // Refresh downloads list
                await fetchDownloads();
                // Remove from search results
                setSearchResults(prev => prev.filter(r => r.doc_id !== docId));
            } else {
                alert(data.error || 'Download failed');
            }
        } catch (error) {
            console.error('Download failed:', error);
        } finally {
            setDownloading(null);
        }
    };

    const handleExtract = async (docId: string) => {
        setExtracting(docId);
        try {
            const res = await fetch(`${API_BASE}/extract/${docId}`, { method: 'POST' });
            const data = await res.json();
            if (data.success && data.data) {
                setExtractedData(prev => ({ ...prev, [docId]: data.data }));
            }
        } catch (error) {
            console.error('Extract failed:', error);
        } finally {
            setExtracting(null);
        }
    };

    const handleViewPdf = (docId: string) => {
        window.open(`${API_BASE}/file/${docId}`, '_blank');
    };

    const formatBytes = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <div className="h-full flex flex-col bg-background text-foreground overflow-y-auto">
            {/* Header */}
            <div className="p-6 border-b border-border bg-card/50">
                <h1 className="text-2xl font-bold tracking-tight flex items-center">
                    <Database className="w-6 h-6 mr-3 text-primary" />
                    Pima County Recorder
                </h1>
                <p className="text-muted-foreground mt-1">
                    Search, download, and extract property data from recorded documents.
                </p>
            </div>

            <div className="p-6 max-w-6xl mx-auto w-full space-y-6">
                {/* Status Card */}
                <div className="p-4 rounded-lg border border-border bg-card flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        {status?.ready ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : (
                            <XCircle className="w-5 h-5 text-yellow-500" />
                        )}
                        <span className="text-sm">
                            {status?.message || 'Checking status...'}
                        </span>
                    </div>
                    <div className="flex items-center space-x-4">
                        <span className="text-xs text-muted-foreground">
                            {downloads.length} documents downloaded
                        </span>
                        <button
                            onClick={() => { fetchStatus(); fetchDownloads(); }}
                            className="p-1.5 rounded hover:bg-muted transition-colors"
                            title="Refresh"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex space-x-2 border-b border-border">
                    <button
                        onClick={() => setActiveTab('downloads')}
                        className={`px-4 py-2 font-medium text-sm transition-colors border-b-2 -mb-[2px] ${activeTab === 'downloads'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        <FileText className="w-4 h-4 inline mr-2" />
                        Downloaded ({downloads.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('search')}
                        className={`px-4 py-2 font-medium text-sm transition-colors border-b-2 -mb-[2px] ${activeTab === 'search'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        <Search className="w-4 h-4 inline mr-2" />
                        Search
                    </button>
                </div>

                {/* Search Tab */}
                {activeTab === 'search' && (
                    <div className="space-y-4">
                        {/* Search Controls */}
                        <div className="p-4 rounded-lg border border-border bg-card flex items-center space-x-4">
                            <select
                                value={selectedDocType}
                                onChange={(e) => setSelectedDocType(e.target.value)}
                                className="flex-1 bg-background border border-border rounded-md px-3 py-2 text-sm"
                            >
                                {DOC_TYPES.map(dt => (
                                    <option key={dt.id} value={dt.id}>{dt.name} - {dt.desc}</option>
                                ))}
                            </select>
                            <button
                                onClick={handleSearch}
                                disabled={searching}
                                className="px-6 py-2 bg-primary text-black font-bold rounded-md hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center"
                            >
                                {searching ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                        Searching...
                                    </>
                                ) : (
                                    <>
                                        <Search className="w-4 h-4 mr-2" />
                                        Search
                                    </>
                                )}
                            </button>
                        </div>

                        {!status?.ready && (
                            <div className="p-4 rounded-lg border border-blue-500/30 bg-blue-500/10 text-blue-200 text-sm flex items-center">
                                <span className="mr-2">ℹ️</span>
                                Session not active. Click <strong>&nbsp;Search&nbsp;</strong> to initialize browser and start searching.
                            </div>
                        )}

                        {/* Search Results */}
                        {searchResults.length > 0 && (
                            <div className="space-y-2">
                                <h3 className="font-semibold text-sm">
                                    Found {searchResults.length} documents
                                </h3>

                                {/* Bulk Actions */}
                                <div className="flex items-center justify-between py-2 border-b border-border/50">
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="checkbox"
                                            checked={searchResults.length > 0 && selectedDocs.size === searchResults.length}
                                            onChange={toggleSelectAll}
                                            className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                                        />
                                        <span className="text-sm text-muted-foreground">Select All</span>
                                    </div>
                                    {selectedDocs.size > 0 && (
                                        <button
                                            onClick={handleBulkDownload}
                                            className="px-3 py-1.5 text-xs font-medium rounded bg-primary text-black hover:bg-primary/90 flex items-center transition-colors"
                                        >
                                            <Download className="w-3 h-3 mr-1" />
                                            Download Selected ({selectedDocs.size})
                                        </button>
                                    )}
                                </div>

                                <div className="grid gap-2">
                                    {searchResults.map(result => (
                                        <div
                                            key={result.doc_id}
                                            className="p-3 rounded border border-border bg-card flex items-center justify-between"
                                        >
                                            <div className="flex items-center space-x-3">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedDocs.has(result.doc_id)}
                                                    onChange={() => toggleSelect(result.doc_id)}
                                                    className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                                                />
                                                <div>
                                                    <span className="font-mono text-sm">{result.doc_number}</span>
                                                    <span className="mx-2 text-muted-foreground">-</span>
                                                    <span className="text-sm">{result.doc_type}</span>
                                                    <span className="mx-2 text-muted-foreground text-xs">({result.record_date})</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => handleDownload(result.doc_id)}
                                                disabled={downloading === result.doc_id}
                                                className="px-3 py-1.5 text-xs font-medium rounded bg-primary text-black hover:bg-primary/90 disabled:opacity-50 flex items-center"
                                            >
                                                {downloading === result.doc_id ? (
                                                    <>
                                                        <Loader2 className="w-3 h-3 animate-spin mr-1" />
                                                        Downloading...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Download className="w-3 h-3 mr-1" />
                                                        Download
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Downloads Tab */}
                {activeTab === 'downloads' && (
                    <div className="space-y-4">
                        {loading ? (
                            <div className="text-center py-10 text-muted-foreground">
                                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
                                <p>Loading documents...</p>
                            </div>
                        ) : downloads.length === 0 ? (
                            <div className="text-center py-10 text-muted-foreground border border-dashed border-border rounded-lg">
                                <FileText className="w-12 h-12 mx-auto mb-3 opacity-20" />
                                <p>No documents downloaded yet.</p>
                                <p className="text-xs mt-1">Use the Search tab to find and download documents.</p>
                            </div>
                        ) : (
                            <div className="grid gap-4">
                                {downloads.map(file => (
                                    <div
                                        key={file.doc_id}
                                        className="p-4 rounded-lg border border-border bg-card hover:border-primary/50 transition-colors"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-2">
                                                    <FileText className="w-4 h-4 text-primary" />
                                                    <span className="font-mono font-semibold">{file.doc_id}</span>
                                                    {file.size_bytes && (
                                                        <span className="text-xs text-muted-foreground">
                                                            ({formatBytes(file.size_bytes)})
                                                        </span>
                                                    )}
                                                </div>

                                                {/* Extracted Data - Enhanced Display */}
                                                {extractedData[file.doc_id] && (
                                                    <div className="mt-3 p-3 rounded bg-primary/5 border border-primary/20 text-sm space-y-2">
                                                        <div className="font-semibold text-primary text-lg">
                                                            {extractedData[file.doc_id].document_type}
                                                        </div>

                                                        {/* Property Address - Highlighted */}
                                                        {extractedData[file.doc_id].property_address && (
                                                            <div className="flex items-start p-2 rounded bg-green-500/10 border border-green-500/30">
                                                                <MapPin className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                                                                <div>
                                                                    <div className="text-xs text-green-400 font-medium">PROPERTY ADDRESS</div>
                                                                    <div className="font-semibold">{extractedData[file.doc_id].property_address}</div>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Parcel Number */}
                                                        {extractedData[file.doc_id].parcel_number && (
                                                            <div className="flex items-center">
                                                                <Home className="w-4 h-4 text-muted-foreground mr-2" />
                                                                <span className="text-muted-foreground">APN:</span>
                                                                <span className="ml-1 font-mono">{extractedData[file.doc_id].parcel_number}</span>
                                                            </div>
                                                        )}

                                                        {/* Parties */}
                                                        <div className="grid grid-cols-2 gap-2">
                                                            {extractedData[file.doc_id].debtor_name && (
                                                                <div className="flex items-center">
                                                                    <User className="w-4 h-4 text-red-400 mr-2" />
                                                                    <span className="text-xs text-muted-foreground">Debtor:</span>
                                                                    <span className="ml-1 text-sm">{extractedData[file.doc_id].debtor_name}</span>
                                                                </div>
                                                            )}
                                                            {extractedData[file.doc_id].creditor_name && (
                                                                <div className="flex items-center">
                                                                    <User className="w-4 h-4 text-blue-400 mr-2" />
                                                                    <span className="text-xs text-muted-foreground">Creditor:</span>
                                                                    <span className="ml-1 text-sm">{extractedData[file.doc_id].creditor_name}</span>
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Amount & Dates */}
                                                        <div className="flex flex-wrap gap-3 text-xs">
                                                            {extractedData[file.doc_id].amount && (
                                                                <div className="flex items-center">
                                                                    <DollarSign className="w-3 h-3 mr-1 text-yellow-500" />
                                                                    {extractedData[file.doc_id].amount}
                                                                </div>
                                                            )}
                                                            {extractedData[file.doc_id].case_number && (
                                                                <div className="text-muted-foreground">
                                                                    Case: {extractedData[file.doc_id].case_number}
                                                                </div>
                                                            )}
                                                            {extractedData[file.doc_id].trustee_sale_date && (
                                                                <div className="flex items-center text-orange-400">
                                                                    <Calendar className="w-3 h-3 mr-1" />
                                                                    Sale: {extractedData[file.doc_id].trustee_sale_date}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Summary */}
                                                        {extractedData[file.doc_id].summary && (
                                                            <div className="text-xs text-muted-foreground mt-2 italic border-t border-border/50 pt-2">
                                                                {extractedData[file.doc_id].summary}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Actions */}
                                            <div className="flex items-center space-x-2 ml-4">
                                                <button
                                                    onClick={() => handleViewPdf(file.doc_id)}
                                                    className="p-2 rounded hover:bg-primary/10 transition-colors"
                                                    title="View PDF"
                                                >
                                                    <Eye className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleExtract(file.doc_id)}
                                                    disabled={extracting === file.doc_id}
                                                    className="px-3 py-1.5 text-xs font-medium rounded bg-primary text-black hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center"
                                                >
                                                    {extracting === file.doc_id ? (
                                                        <>
                                                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                                                            Extracting...
                                                        </>
                                                    ) : extractedData[file.doc_id] ? (
                                                        'Re-extract'
                                                    ) : (
                                                        'Extract Data'
                                                    )}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
