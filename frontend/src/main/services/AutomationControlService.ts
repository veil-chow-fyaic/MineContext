import express from 'express'
import type { Server } from 'http'
import { BrowserWindow } from 'electron'
import type { ScreenSettings } from '../../renderer/src/store/setting'
import type { ScreenMonitorTask } from '../background/task/screen-monitor-task'
import { getLogger } from '@shared/logger/main'

const logger = getLogger('AutomationControlService')

export function startAutomationControlServer(task: ScreenMonitorTask, port = 1734): Server {
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

      res.json({
        success: true,
        data
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      logger.error('start recording failed', error)
      res.status(500).json({
        success: false,
        error: message
      })
    }
  })

  app.post('/recording/stop', (_, res) => {
    task.stopRecording()
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
