import express from 'express'
import type { Server } from 'http'
import { app as electronApp, BrowserWindow, dialog, shell } from 'electron'
import { execFileSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import type { ScreenSettings } from '../../renderer/src/store/setting'
import type { ScreenMonitorTask } from '../background/task/screen-monitor-task'
import { getLogger } from '@shared/logger/main'

const logger = getLogger('AutomationControlService')
const SCREEN_PERMISSION_PROMPT_THROTTLE_MS = 10 * 60 * 1000
let lastScreenPermissionPromptAt = 0

export function startAutomationControlServer(
  task: ScreenMonitorTask,
  port = 1734,
  onRecordingStatusChange?: (isRecording: boolean) => void
): Server {
  const app = express()

  app.use(express.json())

  app.get('/health', (_, res) => {
    res.json({
      success: true,
      service: 'minecontext-automation-control'
    })
  })

  app.get('/recording/status', (_, res) => {
    res.json({
      success: true,
      data: task.getRecordingStatus()
    })
  })

  app.get('/window/status', (_, res) => {
    const mainWindow = BrowserWindow.getAllWindows()[0]
    res.json({
      success: true,
      data: {
        exists: Boolean(mainWindow),
        visible: mainWindow ? mainWindow.isVisible() : false,
        minimized: mainWindow ? mainWindow.isMinimized() : false
      }
    })
  })

  app.get('/ui/status', async (_, res) => {
    const mainWindow = BrowserWindow.getAllWindows()[0]
    const data = await getUiStatus(mainWindow)
    res.json({
      success: true,
      data
    })
  })

  app.post('/window/show', (_, res) => {
    const mainWindow = BrowserWindow.getAllWindows()[0]
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.show()
      mainWindow.focus()
    }
    res.json({
      success: true,
      data: {
        exists: Boolean(mainWindow),
        visible: mainWindow ? mainWindow.isVisible() : false
      }
    })
  })

  app.post('/window/hide', (_, res) => {
    const mainWindow = BrowserWindow.getAllWindows()[0]
    if (mainWindow) {
      mainWindow.hide()
    }
    res.json({
      success: true,
      data: {
        exists: Boolean(mainWindow),
        visible: mainWindow ? mainWindow.isVisible() : false
      }
    })
  })

  app.post('/recording/start', async (req, res) => {
    try {
      const config = (req.body?.config || {}) as Partial<ScreenSettings>
      const data = await task.startRecordingWithDefaults(config)
      onRecordingStatusChange?.(data.status.status === 'running')

      res.json({
        success: true,
        data
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      logger.error('start recording failed', error)
      if (message.includes('No visible screen or window source')) {
        void showScreenRecordingPermissionHelp()
      }
      res.status(500).json({
        success: false,
        error: message,
        permissionHelp: buildScreenRecordingPermissionHelp()
      })
    }
  })

  app.post('/recording/stop', (_, res) => {
    task.stopRecording()
    onRecordingStatusChange?.(false)
    res.json({
      success: true,
      data: task.getRecordingStatus()
    })
  })

  const server = app.listen(port, '127.0.0.1', () => {
    logger.info(`Automation control server listening on http://127.0.0.1:${port}`)
  })

  return server
}

function buildScreenRecordingPermissionHelp() {
  const appBundlePath = getCurrentAppBundlePath()
  return {
    appName: electronApp.getName(),
    bundleId: getCurrentBundleId(appBundlePath),
    executablePath: process.execPath,
    appBundlePath,
    settingsUrl: 'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture',
    message:
      'MineContext is running in development mode, so macOS may list the screen recording permission entry as Electron instead of MineContext.'
  }
}

function getCurrentAppBundlePath(): string {
  if (process.platform !== 'darwin') {
    return process.execPath
  }
  return path.resolve(path.dirname(process.execPath), '..', '..')
}

function getCurrentBundleId(appBundlePath: string): string {
  if (process.platform !== 'darwin') {
    return electronApp.getName()
  }

  const infoPlistPath = path.join(appBundlePath, 'Contents', 'Info.plist')
  if (!existsSync(infoPlistPath)) {
    return 'com.github.Electron'
  }

  try {
    return execFileSync('/usr/libexec/PlistBuddy', ['-c', 'Print :CFBundleIdentifier', infoPlistPath], {
      encoding: 'utf8'
    }).trim()
  } catch {
    return 'com.github.Electron'
  }
}

async function showScreenRecordingPermissionHelp(): Promise<void> {
  if (process.platform !== 'darwin') {
    return
  }

  const now = Date.now()
  if (now - lastScreenPermissionPromptAt < SCREEN_PERMISSION_PROMPT_THROTTLE_MS) {
    return
  }
  lastScreenPermissionPromptAt = now

  const mainWindow = BrowserWindow.getAllWindows()[0]
  const help = buildScreenRecordingPermissionHelp()

  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.show()
    mainWindow.focus()
  }

  const result = await dialog.showMessageBox(mainWindow, {
    type: 'warning',
    title: 'MineContext 需要屏幕录制权限',
    message: 'MineContext 无法获取屏幕源，录制已暂停。',
    detail: [
      '当前是开发态启动，macOS 权限列表里通常显示为 Electron，而不是 MineContext。',
      `请允许屏幕录制权限：Electron (${help.bundleId})`,
      `应用路径：${help.appBundlePath}`,
      '授权后需要重启 MineContext 前端，权限才会对当前进程生效。'
    ].join('\n\n'),
    buttons: ['打开系统设置', '在 Finder 中显示 Electron', '稍后'],
    defaultId: 0,
    cancelId: 2
  })

  if (result.response === 0) {
    await shell.openExternal(help.settingsUrl)
  } else if (result.response === 1) {
    await shell.showItemInFolder(help.appBundlePath)
  }
}

async function getUiStatus(mainWindow: BrowserWindow | undefined): Promise<Record<string, unknown>> {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return {
      exists: false,
      ready: false
    }
  }

  const webContents = mainWindow.webContents
  let rendererState: Record<string, unknown> = {}

  try {
    rendererState = await webContents.executeJavaScript(
      `(() => {
        const text = document.body?.innerText || ''
        const inBootstrapLoading = text.includes('Welcome to MineContext') || text.includes('99%')
        return {
          title: document.title,
          textSample: text.slice(0, 300),
          inBootstrapLoading
        }
      })()`,
      true
    )
  } catch (error) {
    rendererState = {
      error: error instanceof Error ? error.message : String(error)
    }
  }

  const isLoading = webContents.isLoading()
  const isCrashed = webContents.isCrashed()
  const inBootstrapLoading = rendererState.inBootstrapLoading === true

  return {
    exists: true,
    visible: mainWindow.isVisible(),
    minimized: mainWindow.isMinimized(),
    url: webContents.getURL(),
    isLoading,
    isCrashed,
    ready: !isLoading && !isCrashed && !inBootstrapLoading,
    renderer: rendererState
  }
}
