import { useState, useCallback } from 'react';
import { Search, Filter, X, ChevronDown } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';

interface DocumentSearchProps {
  onSearchChange?: (query: string) => void;
  onFilterChange?: (filters: DocumentFilters) => void;
}

export interface DocumentFilters {
  documentType?: string;
  status?: string;
  confidenceMin?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export function DocumentSearch({
  onSearchChange,
  onFilterChange,
}: DocumentSearchProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<DocumentFilters>({});

  const documentTypes = [
    { value: 'invoice', label: 'Invoice' },
    { value: 'receipt', label: 'Receipt' },
    { value: 'quote', label: 'Quote' },
    { value: 'purchase_order', label: 'Purchase Order' },
    { value: 'insurance_claim', label: 'Insurance Claim' },
    { value: 'compliance_form', label: 'Compliance Form' },
  ];

  const statuses = [
    { value: 'uploaded', label: 'Uploaded' },
    { value: 'processing', label: 'Processing' },
    { value: 'completed', label: 'Completed' },
    { value: 'needs_review', label: 'Needs Review' },
    { value: 'failed', label: 'Failed' },
  ];

  const sortOptions = [
    { value: 'created_at', label: 'Created Date' },
    { value: 'filename', label: 'Filename' },
    { value: 'confidence', label: 'Confidence' },
  ];

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearchChange?.(query);
  }, [onSearchChange]);

  const handleFilterChange = useCallback((key: keyof DocumentFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange?.(newFilters);
  }, [filters, onFilterChange]);

  const clearFilters = useCallback(() => {
    const clearedFilters: DocumentFilters = {};
    setFilters(clearedFilters);
    setSearchQuery('');
    onFilterChange?.(clearedFilters);
    onSearchChange?.('');
  }, [onFilterChange, onSearchChange]);

  const activeFilterCount = Object.values(filters).filter(v => v !== undefined).length;

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={handleSearchChange}
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {searchQuery && (
          <button
            onClick={() => {
              setSearchQuery('');
              onSearchChange?.('');
            }}
            className="absolute right-3 top-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Filter Toggle */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <Filter className="h-4 w-4" />
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs">
              {activeFilterCount}
            </span>
          )}
          <ChevronDown
            className={clsx('h-4 w-4 transition-transform', showFilters ? 'rotate-180' : '')}
          />
        </button>

        {activeFilterCount > 0 && (
          <button
            onClick={clearFilters}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="border border-gray-200 rounded-lg p-4 space-y-4">
          {/* Document Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Document Type
            </label>
            <select
              value={filters.documentType || ''}
              onChange={(e) => handleFilterChange('documentType', e.target.value)}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              {documentTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              {statuses.map(status => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>

          {/* Confidence Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Confidence: {filters.confidenceMin ? `${(filters.confidenceMin * 100).toFixed(0)}%` : 'Any'}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.confidenceMin || 0}
              onChange={(e) => handleFilterChange('confidenceMin', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Sort Options */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={filters.sortBy || 'created_at'}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                className="w-full border border-gray-300 rounded-md py-2 px-3 focus:ring-2 focus:ring-blue-500"
              >
                {sortOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order
              </label>
              <select
                value={filters.sortOrder || 'desc'}
                onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                className="w-full border border-gray-300 rounded-md py-2 px-3 focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
