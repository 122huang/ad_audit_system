import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const auditAPI = {
  auditText: (data) => request.post('/audit/text', data),
  auditImage: (formData) => request.post('/audit/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  auditVideo: (data) => request.post('/audit/video', data),
  getMaterials: (params) => request.get('/audit/materials', { params }),
  getMaterial: (id) => request.get(`/audit/materials/${id}`)
}

export const knowledgeAPI = {
  createDocText: (data) => request.post('/knowledge/documents/text', data),
  uploadDoc: (formData) => request.post('/knowledge/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  listDocs: (params) => request.get('/knowledge/documents', { params }),
  deleteDoc: (id) => request.delete(`/knowledge/documents/${id}`),
  createRule: (data) => request.post('/knowledge/rules', data),
  listRules: (params) => request.get('/knowledge/rules', { params }),
  deleteRule: (id) => request.delete(`/knowledge/rules/${id}`),
  createCase: (data) => request.post('/knowledge/cases', data),
  listCases: (params) => request.get('/knowledge/cases', { params })
}

export const regionAPI = {
  list: () => request.get('/regions')
}

export const ruleAPI = {
  list: (params) => request.get('/rules', { params }),
  validate: (data) => request.post('/rules/validate', data)
}

export const advancedAuditAPI = {
  auditR01: (data) => request.post('/advanced-audit/r01', data),
  auditR02: (data) => request.post('/advanced-audit/r02', data)
}

export default request
