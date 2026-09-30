import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

export async function setMode(mode) {
  const res = await client.post('/mode/' + mode)
  return res.data
}

export async function getMode() {
  const res = await client.get('/mode')
  return res.data
}

export async function analyzeTransaction(txid) {
  const res = await client.get('/analyze/transaction/' + txid)
  return res.data
}

export async function getSihTransactionGraph(txid) {
  const res = await client.get('/graph/sih/transaction/' + txid)
  return res.data
}

export async function traceTransaction(txid, depth = 2, limit = 50) {
  const res = await client.get(
    `/trace/transaction/${txid}?depth=${depth}&limit=${limit}`
  )
  return res.data
}

export async function getLiveTransaction(txid) {
  const res = await client.get('/analyze/transaction/' + txid)
  return res.data
}


export async function importDataset(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await client.post('/datasets/import', formData)

  return res.data
}
export async function login(email, password) {
  const res = await client.post('/auth/login', { email, password })
  return res.data
}

export async function signup(email, password, investigator_name) {
  const res = await client.post('/auth/signup', {
    email,
    password,
    investigator_name,
  })
  return res.data
}

