import {
  ChevronLeftIcon,
  ChevronRightIcon,
  DoubleArrowLeftIcon,
  DoubleArrowRightIcon,
} from '@radix-ui/react-icons'
import { type Table } from '@tanstack/react-table'
import { cn, getPageNumbers } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

type DataTablePaginationProps<TData> = {
  table: Table<TData>
  className?: string
}

export function DataTablePagination<TData>({
  table,
  className,
}: DataTablePaginationProps<TData>) {
  const rowCount = table.getFilteredRowModel().rows.length
  const pageSize = table.getState().pagination.pageSize
  const totalPages = Math.max(1, table.getPageCount())
  const pageIndex = Math.min(
    table.getState().pagination.pageIndex,
    totalPages - 1
  )
  const currentPage = pageIndex + 1
  const firstRow = rowCount === 0 ? 0 : pageIndex * pageSize + 1
  const lastRow = Math.min(rowCount, pageIndex * pageSize + pageSize)
  const pageNumbers = getPageNumbers(currentPage, totalPages)

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 overflow-clip px-2',
        '@max-2xl/content:flex-col-reverse @max-2xl/content:gap-4',
        className
      )}
      style={{ overflowClipMargin: 1 }}
    >
      <div className='flex w-full flex-wrap items-center justify-between gap-3'>
        <p className='text-sm text-muted-foreground tabular-nums'>
          Showing{' '}
          <span className='font-medium text-foreground'>
            {firstRow}–{lastRow}
          </span>{' '}
          of <span className='font-medium text-foreground'>{rowCount}</span>
        </p>
        <div className='flex items-center gap-2'>
          <Select
            value={`${pageSize}`}
            onValueChange={(value) => table.setPageSize(Number(value))}
          >
            <SelectTrigger aria-label='Rows per page' className='h-8 w-18'>
              <SelectValue placeholder={pageSize} />
            </SelectTrigger>
            <SelectContent side='top'>
              {[10, 20, 30, 40, 50].map((size) => (
                <SelectItem key={size} value={`${size}`}>
                  {size}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className='hidden text-sm text-muted-foreground sm:inline'>
            per page
          </span>
        </div>
      </div>

      <div className='flex shrink-0 items-center gap-2'>
        <span className='hidden text-sm font-medium whitespace-nowrap text-muted-foreground @max-3xl/content:hidden'>
          Page {currentPage} of {totalPages}
        </span>
        <div className='flex items-center gap-1'>
          <Button
            variant='outline'
            size='icon'
            className='size-8 @max-md/content:hidden'
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage() || rowCount === 0}
            aria-label='Go to first page'
          >
            <DoubleArrowLeftIcon className='size-4' />
          </Button>
          <Button
            variant='outline'
            size='icon'
            className='size-8'
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage() || rowCount === 0}
            aria-label='Go to previous page'
          >
            <ChevronLeftIcon className='size-4' />
          </Button>

          {pageNumbers.map((pageNumber, index) => (
            <div key={`${pageNumber}-${index}`} className='flex items-center'>
              {pageNumber === '...' ? (
                <span className='px-1 text-sm text-muted-foreground'>…</span>
              ) : (
                <Button
                  variant={currentPage === pageNumber ? 'default' : 'outline'}
                  className='h-8 min-w-8 px-2'
                  onClick={() => table.setPageIndex((pageNumber as number) - 1)}
                  disabled={rowCount === 0}
                  aria-current={currentPage === pageNumber ? 'page' : undefined}
                >
                  {pageNumber}
                </Button>
              )}
            </div>
          ))}

          <Button
            variant='outline'
            size='icon'
            className='size-8'
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage() || rowCount === 0}
            aria-label='Go to next page'
          >
            <ChevronRightIcon className='size-4' />
          </Button>
          <Button
            variant='outline'
            size='icon'
            className='size-8 @max-md/content:hidden'
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage() || rowCount === 0}
            aria-label='Go to last page'
          >
            <DoubleArrowRightIcon className='size-4' />
          </Button>
        </div>
      </div>
    </div>
  )
}
