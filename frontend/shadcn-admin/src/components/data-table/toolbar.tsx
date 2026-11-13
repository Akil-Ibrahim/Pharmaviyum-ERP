import { Cross2Icon, MagnifyingGlassIcon } from '@radix-ui/react-icons'
import { type Table } from '@tanstack/react-table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTableFacetedFilter } from './faceted-filter'
import { DataTableViewOptions } from './view-options'

type DataTableToolbarProps<TData> = {
  table: Table<TData>
  searchPlaceholder?: string
  searchKey?: string
  filters?: {
    columnId: string
    title: string
    options: {
      label: string
      value: string
      icon?: React.ComponentType<{ className?: string }>
    }[]
  }[]
}

export function DataTableToolbar<TData>({
  table,
  searchPlaceholder = 'Filter...',
  searchKey,
  filters = [],
}: DataTableToolbarProps<TData>) {
  const searchColumn = searchKey ? table.getColumn(searchKey) : undefined
  const searchValue = searchKey
    ? ((searchColumn?.getFilterValue() as string) ?? '')
    : ((table.getState().globalFilter as string) ?? '')
  const isFiltered =
    table.getState().columnFilters.length > 0 || Boolean(searchValue)

  const setSearchValue = (value: string) => {
    if (searchKey) {
      searchColumn?.setFilterValue(value)
      return
    }
    table.setGlobalFilter(value)
  }

  return (
    <div className='flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
      <div className='flex min-w-0 flex-1 flex-wrap items-center gap-2'>
        <div className='relative w-full min-w-48 sm:max-w-64'>
          <MagnifyingGlassIcon
            aria-hidden='true'
            className='pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground'
          />
          <Input
            aria-label='Search table'
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(event) => setSearchValue(event.target.value)}
            className='h-9 w-full ps-9'
          />
        </div>

        {filters.length > 0 && (
          <div className='flex min-w-0 flex-wrap items-center gap-2'>
            {filters.map((filter) => {
              const column = table.getColumn(filter.columnId)
              if (!column) return null
              return (
                <DataTableFacetedFilter
                  key={filter.columnId}
                  column={column}
                  title={filter.title}
                  options={filter.options}
                />
              )
            })}
          </div>
        )}

        {isFiltered && (
          <Button
            variant='ghost'
            onClick={() => {
              table.resetColumnFilters()
              table.setGlobalFilter('')
            }}
            className='h-9 px-2'
          >
            Reset filters
            <Cross2Icon className='ms-2 size-4' />
          </Button>
        )}
      </div>

      <DataTableViewOptions table={table} />
    </div>
  )
}
