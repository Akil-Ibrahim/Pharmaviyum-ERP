import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { ChevronDownIcon } from '@radix-ui/react-icons'
import { zodResolver } from '@hookform/resolvers/zod'
import { fonts } from '@/config/fonts'
import { Check } from 'lucide-react'
import { showSubmittedData } from '@/lib/show-submitted-data'
import { cn } from '@/lib/utils'
import { useFont } from '@/context/font-provider'
import {
  getNavIconColor,
  NAVIGATION_ICON_COLORS,
  type NavigationIconColor,
  type NavigationIconPreset,
  useTheme,
} from '@/context/theme-provider'
import { Button, buttonVariants } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'

const appearanceFormSchema = z.object({
  theme: z.enum(['light', 'dark']),
  font: z.enum(fonts),
  navigationIconColor: z
    .string()
    .refine(
      (value) =>
        value in NAVIGATION_ICON_COLORS || /^#[\da-fA-F]{6}$/.test(value),
      'Choose a preset or enter a valid 6-digit HEX color.'
    ),
})

type AppearanceFormValues = z.infer<typeof appearanceFormSchema>

export function AppearanceForm() {
  const { font, setFont } = useFont()
  const { theme, setTheme, navigationIconColor, setNavigationIconColor } =
    useTheme()

  const defaultValues: Partial<AppearanceFormValues> = {
    theme: theme as 'light' | 'dark',
    font,
    navigationIconColor,
  }

  const form = useForm<AppearanceFormValues>({
    resolver: zodResolver(appearanceFormSchema),
    defaultValues,
  })

  function onSubmit(data: AppearanceFormValues) {
    if (data.font != font) setFont(data.font)
    if (data.theme != theme) setTheme(data.theme)
    if (data.navigationIconColor !== navigationIconColor) {
      setNavigationIconColor(data.navigationIconColor as NavigationIconColor)
    }

    showSubmittedData(data)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className='space-y-8'>
        <FormField
          control={form.control}
          name='font'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Font</FormLabel>
              <div className='relative w-max'>
                <FormControl>
                  <select
                    className={cn(
                      buttonVariants({ variant: 'outline' }),
                      'w-50 appearance-none font-normal capitalize',
                      'dark:bg-background dark:hover:bg-background'
                    )}
                    {...field}
                  >
                    {fonts.map((font) => (
                      <option key={font} value={font}>
                        {font}
                      </option>
                    ))}
                  </select>
                </FormControl>
                <ChevronDownIcon className='absolute inset-e-3 top-2.5 h-4 w-4 opacity-50' />
              </div>
              <FormDescription className='font-manrope'>
                Set the font you want to use in the dashboard.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='theme'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Theme</FormLabel>
              <FormDescription>
                Select the theme for the dashboard.
              </FormDescription>
              <FormMessage />
              <RadioGroup
                onValueChange={field.onChange}
                defaultValue={field.value}
                className='grid max-w-md grid-cols-2 gap-8 pt-2'
              >
                <FormItem>
                  <FormLabel className='[&:has([data-state=checked])>div]:border-primary'>
                    <FormControl>
                      <RadioGroupItem value='light' className='sr-only' />
                    </FormControl>
                    <div className='items-center rounded-md border-2 border-muted p-1 hover:border-accent'>
                      <div className='space-y-2 rounded-sm bg-[#ecedef] p-2'>
                        <div className='space-y-2 rounded-md bg-white p-2 shadow-xs'>
                          <div className='h-2 w-20 rounded-lg bg-[#ecedef]' />
                          <div className='h-2 w-25 rounded-lg bg-[#ecedef]' />
                        </div>
                        <div className='flex items-center space-x-2 rounded-md bg-white p-2 shadow-xs'>
                          <div className='h-4 w-4 rounded-full bg-[#ecedef]' />
                          <div className='h-2 w-25 rounded-lg bg-[#ecedef]' />
                        </div>
                        <div className='flex items-center space-x-2 rounded-md bg-white p-2 shadow-xs'>
                          <div className='h-4 w-4 rounded-full bg-[#ecedef]' />
                          <div className='h-2 w-25 rounded-lg bg-[#ecedef]' />
                        </div>
                      </div>
                    </div>
                    <span className='block w-full p-2 text-center font-normal'>
                      Light
                    </span>
                  </FormLabel>
                </FormItem>
                <FormItem>
                  <FormLabel className='[&:has([data-state=checked])>div]:border-primary'>
                    <FormControl>
                      <RadioGroupItem value='dark' className='sr-only' />
                    </FormControl>
                    <div className='items-center rounded-md border-2 border-muted bg-popover p-1 hover:bg-accent hover:text-accent-foreground'>
                      <div className='space-y-2 rounded-sm bg-slate-950 p-2'>
                        <div className='space-y-2 rounded-md bg-slate-800 p-2 shadow-xs'>
                          <div className='h-2 w-20 rounded-lg bg-slate-400' />
                          <div className='h-2 w-25 rounded-lg bg-slate-400' />
                        </div>
                        <div className='flex items-center space-x-2 rounded-md bg-slate-800 p-2 shadow-xs'>
                          <div className='h-4 w-4 rounded-full bg-slate-400' />
                          <div className='h-2 w-25 rounded-lg bg-slate-400' />
                        </div>
                        <div className='flex items-center space-x-2 rounded-md bg-slate-800 p-2 shadow-xs'>
                          <div className='h-4 w-4 rounded-full bg-slate-400' />
                          <div className='h-2 w-25 rounded-lg bg-slate-400' />
                        </div>
                      </div>
                    </div>
                    <span className='block w-full p-2 text-center font-normal'>
                      Dark
                    </span>
                  </FormLabel>
                </FormItem>
              </RadioGroup>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name='navigationIconColor'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Navigation icon colour</FormLabel>
              <FormDescription>
                Choose a preset or define your own HEX colour. This preference
                is saved for future visits. Active icon tiles use a white icon;
                the dashboard background remains unchanged.
              </FormDescription>
              <FormControl>
                <div
                  role='group'
                  aria-label='Navigation icon colour'
                  className='space-y-4'
                >
                  <div className='grid max-w-xl grid-cols-2 gap-2 sm:grid-cols-3'>
                    {(
                      Object.keys(
                        NAVIGATION_ICON_COLORS
                      ) as NavigationIconPreset[]
                    ).map((name) => {
                      const selected = field.value === name
                      return (
                        <Button
                          key={name}
                          type='button'
                          variant='outline'
                          aria-pressed={selected}
                          onClick={() => field.onChange(name)}
                          className={cn(
                            'h-10 justify-start gap-2.5 rounded-lg px-3 font-normal capitalize',
                            selected && 'border-primary bg-accent/50'
                          )}
                        >
                          <span
                            aria-hidden='true'
                            className='size-3.5 shrink-0 rounded-full ring-1 ring-black/10'
                            style={{
                              backgroundColor: NAVIGATION_ICON_COLORS[name],
                            }}
                          />
                          <span className='truncate'>{name}</span>
                          {selected && (
                            <Check
                              aria-hidden='true'
                              className='ms-auto size-4'
                            />
                          )}
                        </Button>
                      )
                    })}
                  </div>
                  <div className='flex flex-wrap items-end gap-3'>
                    <div className='space-y-2'>
                      <FormLabel htmlFor='navigation-icon-color-picker'>
                        Custom colour
                      </FormLabel>
                      <Input
                        id='navigation-icon-color-picker'
                        type='color'
                        aria-label='Pick custom navigation icon colour'
                        value={getNavIconColor(
                          field.value as NavigationIconColor
                        )}
                        onChange={(event) =>
                          field.onChange(event.target.value.toUpperCase())
                        }
                        className='h-10 w-16 cursor-pointer p-1'
                      />
                    </div>
                    <div className='space-y-2'>
                      <FormLabel htmlFor='navigation-icon-color-hex'>
                        HEX value
                      </FormLabel>
                      <Input
                        id='navigation-icon-color-hex'
                        value={getNavIconColor(
                          field.value as NavigationIconColor
                        ).toUpperCase()}
                        onChange={(event) =>
                          field.onChange(event.target.value.trim())
                        }
                        placeholder='#2563EB'
                        maxLength={7}
                        className='w-36 font-mono uppercase'
                      />
                    </div>
                    <span
                      aria-hidden='true'
                      className='mb-1 size-5 rounded-full border'
                      style={{
                        backgroundColor: getNavIconColor(
                          field.value as NavigationIconColor
                        ),
                      }}
                    />
                  </div>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type='submit'>Update preferences</Button>
      </form>
    </Form>
  )
}
