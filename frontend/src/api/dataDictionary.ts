import apiClient from './client';

export interface RegulatoryDataDictionaryEntry {
  dict_id: number;
  report_name: string;
  schedule_name: string;
  line_item_number?: string;
  line_item_name: string;
  technical_line_item_name?: string;
  mdrm?: string;
  description?: string;
  static_or_dynamic?: string;
  mandatory_or_optional?: string;
  format_specification?: string;
  num_reports_schedules_used?: string;
  other_schedule_reference?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataDictionaryListResponse {
  items: RegulatoryDataDictionaryEntry[];
  total: number;
  page: number;
  per_page: number;
}

export interface DataDictionaryFilter {
  report_name?: string;
  schedule_name?: string;
  line_item_name?: string;
  mandatory_or_optional?: string;
  static_or_dynamic?: string;
  search?: string;
  is_active?: boolean;
}

export interface DataDictionaryImportRequest {
  selected_dict_ids: number[];
  cycle_id: number;
  report_id: number;
  import_options?: Record<string, any>;
}

export interface DataDictionaryImportResponse {
  success: boolean;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  messages: string[];
  created_attributes: number[];
}

export interface DataDictionaryStats {
  total_entries: number;
  total_reports: number;
  total_schedules: number;
  mandatory_count: number;
  optional_count: number;
}

class DataDictionaryAPI {
  async getDataDictionary(
    page: number = 1,
    perPage: number = 50,
    filters?: DataDictionaryFilter
  ): Promise<DataDictionaryListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          // Don't use params.append for values with special characters
          // The URLSearchParams will handle encoding automatically
          params.set(key, value.toString());
        }
      });
    }

    const response = await apiClient.get(`/data-dictionary/?${params.toString()}`);
    return response.data;
  }

  async getAvailableReports(): Promise<string[]> {
    const response = await apiClient.get('/data-dictionary/reports/');
    return response.data;
  }

  async getAvailableSchedules(reportName?: string): Promise<string[]> {
    const params = reportName ? `?report_name=${encodeURIComponent(reportName)}` : '';
    const response = await apiClient.get(`/data-dictionary/schedules${params}`);
    return response.data;
  }

  async importDataDictionaryEntries(
    importRequest: DataDictionaryImportRequest
  ): Promise<DataDictionaryImportResponse> {
    const response = await apiClient.post('/data-dictionary/import/', importRequest);
    return response.data;
  }

  async reloadDataDictionary(clearExisting: boolean = false): Promise<any> {
    const params = clearExisting ? '?clear_existing=true' : '';
    const response = await apiClient.post(`/data-dictionary/reload${params}`);
    return response.data;
  }

  async getDataDictionaryStats(): Promise<DataDictionaryStats> {
    const response = await apiClient.get('/data-dictionary/stats/');
    return response.data;
  }
}

export const dataDictionaryAPI = new DataDictionaryAPI(); 