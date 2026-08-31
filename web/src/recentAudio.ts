const DB_NAME = 'djtransgan.recentAudio'
const DB_VERSION = 1
const STORE = 'files'
const MAX_RECENT = 12

export interface RecentFileMeta {
  id: string
  name: string
  size: number
  lastModified: number
  type: string
  addedAt: number
}

interface RecentFileRecord extends RecentFileMeta {
  blob: Blob
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' })
        store.createIndex('addedAt', 'addedAt')
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error ?? new Error('indexedDB open failed'))
  })
}

function reqToPromise<T>(req: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error ?? new Error('indexedDB request failed'))
  })
}

export function fileIdentity(file: File): string {
  return `${file.name}::${file.size}::${file.lastModified}`
}

export async function rememberRecentFile(file: File): Promise<string> {
  const id = fileIdentity(file)
  const db = await openDb()
  try {
    const tx = db.transaction(STORE, 'readwrite')
    const store = tx.objectStore(STORE)
    const record: RecentFileRecord = {
      id,
      name: file.name,
      size: file.size,
      lastModified: file.lastModified,
      type: file.type || 'audio/*',
      addedAt: Date.now(),
      blob: file,
    }
    store.put(record)
    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error ?? new Error('indexedDB write failed'))
    })
    await trimRecent(db)
  } finally {
    db.close()
  }
  return id
}

async function trimRecent(db: IDBDatabase) {
  const tx = db.transaction(STORE, 'readwrite')
  const store = tx.objectStore(STORE)
  const all = (await reqToPromise(store.getAll())) as RecentFileRecord[]
  all.sort((a, b) => b.addedAt - a.addedAt)
  const drop = all.slice(MAX_RECENT)
  for (const item of drop) store.delete(item.id)
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error ?? new Error('indexedDB trim failed'))
  })
}

export async function listRecentMeta(): Promise<RecentFileMeta[]> {
  const db = await openDb()
  try {
    const tx = db.transaction(STORE, 'readonly')
    const store = tx.objectStore(STORE)
    const all = (await reqToPromise(store.getAll())) as RecentFileRecord[]
    return all
      .map(({ id, name, size, lastModified, type, addedAt }) => ({
        id,
        name,
        size,
        lastModified,
        type,
        addedAt,
      }))
      .sort((a, b) => b.addedAt - a.addedAt)
  } finally {
    db.close()
  }
}

export async function getRecentBlob(id: string): Promise<Blob | null> {
  const db = await openDb()
  try {
    const tx = db.transaction(STORE, 'readonly')
    const store = tx.objectStore(STORE)
    const row = (await reqToPromise(store.get(id))) as RecentFileRecord | undefined
    return row?.blob ?? null
  } finally {
    db.close()
  }
}

export async function removeRecent(id: string): Promise<void> {
  const db = await openDb()
  try {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).delete(id)
    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error ?? new Error('indexedDB delete failed'))
    })
  } finally {
    db.close()
  }
}
