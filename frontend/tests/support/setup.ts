import { config } from '@vue/test-utils';

import { RouterLinkStub } from './router';

/**
 * 全局测试装置。
 *
 * 单元测试不安装真实 router，`RouterLink` 拿不到注入的实例会报
 * “Failed to resolve component”。这里用 VTU 的全局 `config` 挂一个
 * 只渲染 `to` 的 `<a>` 桩，各 spec 无需各自声明 `stubs`。
 */
config.global.stubs = { ...config.global.stubs, RouterLink: RouterLinkStub };
