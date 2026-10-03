/**
 * API 客户端的公共错误类型。
 *
 * 面板计算与预设拉取各自抛出带 `status` 的错误，UI 据此区分
 * 「后端返回了可展示的 detail」与「网络不可达」，因此共用一个基类，
 * 调用方也可以一次捕获两类失败。
 */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** 面板计算失败。 */
export class PanelApiError extends ApiError {
  constructor(message: string, status: number) {
    super(message, status);
    this.name = 'PanelApiError';
  }
}

/**
 * 预设数据拉取失败。
 *
 * 后端在数据非法时返回 503（数据源坏了），与面板计算的 4xx/5xx 语义不同，
 * 但都意味着「预设下拉不可用」。
 */
export class PresetApiError extends ApiError {
  constructor(message: string, status: number) {
    super(message, status);
    this.name = 'PresetApiError';
  }
}