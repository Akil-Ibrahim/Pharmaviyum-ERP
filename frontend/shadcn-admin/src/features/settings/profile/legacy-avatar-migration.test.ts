import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const uploadProfileAvatar = vi.hoisted(() => vi.fn())

vi.mock('./api', () => ({ uploadProfileAvatar }))

import { migrateLegacyAvatarOnce } from './legacy-avatar-migration'

const validPngDataUrl = 'data:image/png;base64,dGVzdA=='

function stubImageFetch(blob: Blob) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      blob: vi.fn().mockResolvedValue(blob),
    } as unknown as Response)
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('migrateLegacyAvatarOnce', () => {
  it('uploads a valid legacy image as a File', async () => {
    stubImageFetch(new Blob(['image-bytes'], { type: 'image/png' }))
    uploadProfileAvatar.mockResolvedValue(undefined)

    await expect(
      migrateLegacyAvatarOnce('account-1', validPngDataUrl)
    ).resolves.toBe(true)

    expect(uploadProfileAvatar).toHaveBeenCalledTimes(1)
    const uploadedFile = uploadProfileAvatar.mock.calls[0][0]
    expect(uploadedFile).toBeInstanceOf(File)
    expect(uploadedFile.type).toBe('image/png')
    expect(uploadedFile.name).toBe('profile-avatar')
  })

  it('does not upload unsupported image formats', async () => {
    stubImageFetch(new Blob(['image-bytes'], { type: 'image/gif' }))

    await expect(
      migrateLegacyAvatarOnce('account-2', 'data:image/gif;base64,dGVzdA==')
    ).resolves.toBe(false)

    expect(uploadProfileAvatar).not.toHaveBeenCalled()
  })

  it('does not upload images larger than 2 MB', async () => {
    const oversizedImage = new Blob(
      [new Uint8Array(2 * 1024 * 1024 + 1)],
      { type: 'image/png' }
    )
    stubImageFetch(oversizedImage)

    await expect(
      migrateLegacyAvatarOnce('account-3', validPngDataUrl)
    ).resolves.toBe(false)

    expect(uploadProfileAvatar).not.toHaveBeenCalled()
  })

  it('allows a later retry after an upload failure', async () => {
    stubImageFetch(new Blob(['image-bytes'], { type: 'image/png' }))
    uploadProfileAvatar
      .mockRejectedValueOnce(new Error('Upload failed'))
      .mockResolvedValueOnce(undefined)

    await expect(
      migrateLegacyAvatarOnce('account-retry', validPngDataUrl)
    ).rejects.toThrow('Upload failed')

    await expect(
      migrateLegacyAvatarOnce('account-retry', validPngDataUrl)
    ).resolves.toBe(true)

    expect(uploadProfileAvatar).toHaveBeenCalledTimes(2)
  })

  it('shares one in-flight upload between consumers of the same account', async () => {
    stubImageFetch(new Blob(['image-bytes'], { type: 'image/png' }))

    let finishUpload!: () => void
    let markUploadStarted!: () => void
    const uploadStarted = new Promise<void>((resolve) => {
      markUploadStarted = resolve
    })
    uploadProfileAvatar.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          finishUpload = resolve
          markUploadStarted()
        })
    )

    const first = migrateLegacyAvatarOnce('account-4', validPngDataUrl)
    const second = migrateLegacyAvatarOnce('account-4', validPngDataUrl)

    await uploadStarted
    expect(uploadProfileAvatar).toHaveBeenCalledTimes(1)

    finishUpload()
    await expect(Promise.all([first, second])).resolves.toEqual([true, true])
  })
})
