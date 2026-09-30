import { useRef, useState } from 'react'
import { importDataset } from '../api'
import {
  Upload,
  FileText,
  FileJson,
  FileCode2,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Database,
  ShieldCheck,
} from 'lucide-react'

const MAX_FILE_SIZE = 100 * 1024 * 1024

const REQUIRED_COLUMN_ALIASES = {
  transaction_id: [
    'transaction_id',
    'txid',
    'transaction',
    'hash',
    'tx_hash',
  ],
  timestamp: [
    'timestamp',
    'timestamp_utc',
    'time',
    'datetime',
    'date',
  ],
  bitcoin_transferred: [
    'bitcoin_transferred',
    'amount_btc',
    'btc_amount',
    'amount',
    'value_btc',
  ],
  wallet_address: [
    'wallet_address',
    'sender_wallet',
    'receiver_wallet',
    'sender_address',
    'receiver_address',
    'from_wallet',
    'to_wallet',
    'from_address',
    'to_address',
    'source_wallet',
    'destination_wallet',
  ],
  ip_address: [
    'ip_address',
    'sender_ip',
    'receiver_ip',
    'source_ip',
    'destination_ip',
    'from_ip',
    'to_ip',
  ],
  port_no: [
    'port_no',
    'source_port',
    'sender_port',
    'src_port',
    'dest_port',
    'destination_port',
    'receiver_port',
    'dst_port',
  ],
}
const SUPPORTED_TYPES = {
  csv: {
    label: 'CSV',
    icon: FileText,
    extensions: ['.csv'],
  },
  json: {
    label: 'JSON',
    icon: FileJson,
    extensions: ['.json'],
  },
  xml: {
    label: 'XML',
    icon: FileCode2,
    extensions: ['.xml'],
  },
}

function getExtension(filename) {
  const index = filename.lastIndexOf('.')

  if (index === -1) {
    return ''
  }

  return filename.substring(index).toLowerCase()
}

function getFileType(filename) {
  const extension = getExtension(filename)

  if (extension === '.csv') return 'csv'
  if (extension === '.json') return 'json'
  if (extension === '.xml') return 'xml'

  return null
}

function parseCsv(text) {
  const rows = []
  let row = []
  let cell = ''
  let insideQuotes = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    const next = text[i + 1]

    if (char === '"') {
      if (insideQuotes && next === '"') {
        cell += '"'
        i += 1
      } else {
        insideQuotes = !insideQuotes
      }
      continue
    }

    if (char === ',' && !insideQuotes) {
      row.push(cell)
      cell = ''
      continue
    }

    if ((char === '\n' || char === '\r') && !insideQuotes) {
      if (char === '\r' && next === '\n') {
        i += 1
      }

      row.push(cell)
      cell = ''

      if (row.some((value) => value.trim() !== '')) {
        rows.push(row)
      }

      row = []
      continue
    }

    cell += char
  }

  if (cell !== '' || row.length > 0) {
    row.push(cell)

    if (row.some((value) => value.trim() !== '')) {
      rows.push(row)
    }
  }

  if (rows.length === 0) {
    throw new Error('CSV file is empty.')
  }

  const headers = rows[0].map((header) => header.trim())

  if (headers.length === 0) {
    throw new Error('CSV header row is missing.')
  }

  const dataRows = rows.slice(1).map((values) => {
    const record = {}

    headers.forEach((header, index) => {
      record[header] = (values[index] ?? '').trim()
    })

    return record
  })

  return {
    headers,
    rows: dataRows,
  }
}

function parseJson(text) {
  let parsed

  try {
    parsed = JSON.parse(text)
  } catch {
    throw new Error('Invalid JSON syntax.')
  }

  if (Array.isArray(parsed)) {
    if (parsed.length === 0) {
      throw new Error('JSON array is empty.')
    }

    if (
      typeof parsed[0] !== 'object' ||
      parsed[0] === null ||
      Array.isArray(parsed[0])
    ) {
      throw new Error('JSON must contain an array of transaction objects.')
    }

    return {
      headers: Object.keys(parsed[0]),
      rows: parsed,
    }
  }

  if (
    typeof parsed === 'object' &&
    parsed !== null &&
    Array.isArray(parsed.transactions)
  ) {
    if (parsed.transactions.length === 0) {
      throw new Error('JSON transactions array is empty.')
    }

    return {
      headers: Object.keys(parsed.transactions[0]),
      rows: parsed.transactions,
    }
  }

  throw new Error(
    'JSON must be an array of transaction objects or contain a transactions array.'
  )
}

function parseXml(text) {
  const parser = new DOMParser()
  const document = parser.parseFromString(text, 'application/xml')

  const parserError = document.querySelector('parsererror')

  if (parserError) {
    throw new Error('Invalid XML syntax.')
  }

  const transactionNodes = Array.from(
    document.querySelectorAll('transaction')
  )

  if (transactionNodes.length === 0) {
    throw new Error(
      'No <transaction> elements were found in the XML dataset.'
    )
  }

  const rows = transactionNodes.map((transaction) => {
    const record = {}

    Array.from(transaction.children).forEach((child) => {
      record[child.tagName] = child.textContent?.trim() ?? ''
    })

    return record
  })

  return {
    headers: Object.keys(rows[0]),
    rows,
  }
}

function validateRows(rows, headers) {
  const normalizedHeaders = headers.map((header) =>
    String(header).trim().toLowerCase()
  )

  const resolvedColumns = {}

  Object.entries(REQUIRED_COLUMN_ALIASES).forEach(
    ([canonicalColumn, aliases]) => {
      const matchedHeader = aliases.find((alias) =>
        normalizedHeaders.includes(alias)
      )

      if (matchedHeader) {
        const originalHeader = headers[normalizedHeaders.indexOf(matchedHeader)]
        resolvedColumns[canonicalColumn] = originalHeader
      }
    }
  )

  const missingColumns = Object.keys(REQUIRED_COLUMN_ALIASES).filter(
    (column) => !resolvedColumns[column]
  )

  if (missingColumns.length > 0) {
    return {
      valid: false,
      missingColumns,
      invalidRows: 0,
      emptyRequiredValues: 0,
      resolvedColumns,
    }
  }

  let invalidRows = 0
  let emptyRequiredValues = 0

  rows.forEach((row) => {
    let rowInvalid = false

    Object.entries(resolvedColumns).forEach(
      ([canonicalColumn, originalColumn]) => {
        const value = row[originalColumn]

        if (
          value === undefined ||
          value === null ||
          String(value).trim() === ''
        ) {
          emptyRequiredValues += 1
          rowInvalid = true
        }
      }
    )

    const port = Number(row[resolvedColumns.port_no])
    const bitcoin = Number(row[resolvedColumns.bitcoin_transferred])

    if (!Number.isFinite(port) || port < 0 || port > 65535) {
      rowInvalid = true
    }

    if (!Number.isFinite(bitcoin) || bitcoin < 0) {
      rowInvalid = true
    }

    if (rowInvalid) {
      invalidRows += 1
    }
  })

  return {
    valid: invalidRows === 0,
    missingColumns: [],
    invalidRows,
    emptyRequiredValues,
    resolvedColumns,
  }
}


export default function DataSources() {
  const inputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validation, setValidation] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const validateFileSelection = (selectedFile) => {
    setError('')
    setValidation(null)
    setAnalysis(null)

    if (!selectedFile) {
      setFile(null)
      return
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setFile(null)
      setError('File size must be 100 MB or less.')
      return
    }

    const fileType = getFileType(selectedFile.name)

    if (!fileType) {
      setFile(null)
      setError('Unsupported file format. Please select CSV, JSON or XML.')
      return
    }

    setFile(selectedFile)
  }

  const handleFileChange = (event) => {
    validateFileSelection(event.target.files?.[0])
  }

  const handleDrop = (event) => {
    event.preventDefault()
    validateFileSelection(event.dataTransfer.files?.[0])
  }

  const removeFile = () => {
    setFile(null)
    setError('')
    setValidation(null)
    setAnalysis(null)

    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const handleValidate = async () => {
    if (!file) return

    setIsValidating(true)
    setError('')
    setValidation(null)

    try {
      const text = await file.text()
      const fileType = getFileType(file.name)

      let parsed

      if (fileType === 'csv') {
        parsed = parseCsv(text)
      } else if (fileType === 'json') {
        parsed = parseJson(text)
      } else {
        parsed = parseXml(text)
      }

      const result = validateRows(parsed.rows, parsed.headers)

      setValidation({
        ...result,
        format: fileType.toUpperCase(),
        fileName: file.name,
        rowCount: parsed.rows.length,
        columnCount: parsed.headers.length,
      })
    } catch (validationError) {
      setError(
        validationError instanceof Error
          ? validationError.message
          : 'Dataset validation failed.'
      )
    } finally {
      setIsValidating(false)
    }
  }

  const handleAnalyze = async () => {
    if (!file || !validation?.valid) return

    setIsAnalyzing(true)
    setError('')
    setAnalysis(null)

    try {
      const result = await importDataset(file)
      setAnalysis(result)
    } catch (analysisError) {
      setError(
        analysisError?.response?.data?.detail ||
          analysisError?.message ||
          'Dataset analysis failed.'
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const analysisSummary = analysis
    ? [
        {
          label: 'Rows analyzed',
          value: analysis.total_rows ?? 0,
        },
        {
          label: 'Transactions',
          value: analysis.transactions_analyzed ?? 0,
        },
        {
          label: 'Anomalous signals',
          value: analysis.anomalous_signals ?? 0,
        },
        {
          label: 'IP entities',
          value: analysis.ip_entities ?? 0,
        },
        {
          label: 'Wallet entities',
          value: analysis.wallet_entities ?? 0,
        },
        {
          label: 'Transaction entities',
          value: analysis.transaction_entities ?? 0,
        },
      ]
    : []

  return (
    <div className="min-h-full bg-slate-50 p-6 lg:p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
              <Database size={22} />
            </div>

            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                Import Dataset
              </h1>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                Import transaction and network data for ChainShield
                investigation and analysis.
              </p>
            </div>
          </div>
        </div>

        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-blue-600" />

            <h2 className="text-sm font-semibold text-slate-900">
              Supported dataset formats
            </h2>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {Object.entries(SUPPORTED_TYPES).map(
              ([key, { label, icon: Icon }]) => (
                <div
                  key={key}
                  className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <Icon size={20} className="text-blue-600" />

                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {label}
                    </p>

                    <p className="text-xs text-slate-500">
                      {key === 'csv'
                        ? 'Comma-separated transaction data'
                        : key === 'json'
                          ? 'Structured transaction objects'
                          : 'Structured XML transactions'}
                    </p>
                  </div>
                </div>
              )
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Select dataset
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Select a dataset and validate its structure before analysis.
          </p>

          <div
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDrop}
            className="mt-6 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center transition hover:border-blue-400 hover:bg-blue-50/30"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <Upload size={25} />
            </div>

            <h3 className="mt-4 text-base font-semibold text-slate-900">
              Drop your dataset here
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              or select a file from your computer
            </p>

            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="mt-5 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
            >
              Browse Files
            </button>

            <input
              ref={inputRef}
              type="file"
              accept=".csv,.json,.xml"
              onChange={handleFileChange}
              className="hidden"
            />

            <p className="mt-4 text-xs text-slate-500">
              CSV Â· JSON Â· XML Â· Maximum size 100 MB
            </p>
          </div>

          {error && (
            <div className="mt-5 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
              <AlertCircle
                size={20}
                className="mt-0.5 shrink-0 text-red-600"
              />

              <div>
                <p className="text-sm font-semibold text-red-800">
                  Validation error
                </p>

                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {file && (
            <div className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                    <FileText size={20} />
                  </div>

                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">
                      {file.name}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {formatSize(file.size)} Â· Ready for validation
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={removeFile}
                  className="rounded-md p-2 text-slate-500 transition hover:bg-slate-100 hover:text-red-600"
                  title="Remove file"
                >
                  <X size={18} />
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button
              type="button"
              disabled={!file || isValidating}
              onClick={handleValidate}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isValidating && <Loader2 size={17} className="animate-spin" />}
              {isValidating ? 'Validating...' : 'Validate Dataset'}
            </button>
          </div>

          {validation && (
            <div
              className={`mt-6 rounded-xl border p-5 ${
                validation.valid
                  ? 'border-green-200 bg-green-50'
                  : 'border-amber-200 bg-amber-50'
              }`}
            >
              <div className="flex items-start gap-3">
                {validation.valid ? (
                  <CheckCircle2
                    size={22}
                    className="mt-0.5 shrink-0 text-green-600"
                  />
                ) : (
                  <AlertCircle
                    size={22}
                    className="mt-0.5 shrink-0 text-amber-600"
                  />
                )}

                <div className="min-w-0">
                  <h3
                    className={`text-base font-semibold ${
                      validation.valid
                        ? 'text-green-900'
                        : 'text-amber-900'
                    }`}
                  >
                    {validation.valid
                      ? 'Dataset validation passed'
                      : 'Dataset validation requires attention'}
                  </h3>

                  <p
                    className={`mt-1 text-sm ${
                      validation.valid
                        ? 'text-green-800'
                        : 'text-amber-800'
                    }`}
                  >
                    {validation.valid
                      ? 'The dataset contains the required ChainShield fields and passed the local data checks.'
                      : 'The dataset could not pass all required data checks.'}
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-white/70 bg-white/70 p-3">
                  <p className="text-xs text-slate-500">Format</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {validation.format}
                  </p>
                </div>

                <div className="rounded-lg border border-white/70 bg-white/70 p-3">
                  <p className="text-xs text-slate-500">Records</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {validation.rowCount.toLocaleString()}
                  </p>
                </div>

                <div className="rounded-lg border border-white/70 bg-white/70 p-3">
                  <p className="text-xs text-slate-500">Columns</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {validation.columnCount}
                  </p>
                </div>

                <div className="rounded-lg border border-white/70 bg-white/70 p-3">
                  <p className="text-xs text-slate-500">Invalid rows</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {validation.invalidRows.toLocaleString()}
                  </p>
                </div>
              </div>

              {validation.missingColumns?.length > 0 && (
                <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
                  <p className="text-sm font-semibold text-red-800">
                    Missing required columns
                  </p>

                  <p className="mt-1 text-sm text-red-700">
                    {validation.missingColumns.join(', ')}
                  </p>
                </div>
              )}

              {validation.emptyRequiredValues > 0 && (
                <div className="mt-4 rounded-lg border border-amber-200 bg-white/60 p-4">
                  <p className="text-sm text-amber-800">
                    Empty required values detected:{' '}
                    <span className="font-semibold">
                      {validation.emptyRequiredValues.toLocaleString()}
                    </span>
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="mt-5 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <p className="text-sm leading-6 text-blue-800">
            Dataset validation runs locally in your browser. The selected file
            is not transmitted to an external service by this interface.
          </p>
        </div>
      </div>
    </div>
  )
}


