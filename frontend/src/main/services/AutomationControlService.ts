import express from 'express'
import type { Server } from 'http'
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
