// Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
// SPDX-License-Identifier: Apache-2.0

import { app } from 'electron'
import path from 'path'

import { getDataPath } from './utils'
const isDev = process.env.NODE_ENV === 'development'

const userDataDir = process.env.MINECONTEXT_USER_DATA_DIR

if (userDataDir) {
  app.setPath('userData', path.resolve(userDataDir))
} else if (isDev) {
  app.setPath('userData', app.getPath('userData') + 'Dev')
}

export const DATA_PATH = getDataPath()
