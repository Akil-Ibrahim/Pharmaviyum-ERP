import {
  Activity,
  ArrowRight,
  Bot,
  Bug,
  CheckCircle2,
  CircleDashed,
  FlaskConical,
  GitBranch,
  ShieldCheck,
} from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Main } from '@/components/layout/main'
import { PageHeader } from '@/components/page-header'

const capabilities = [
  {
    title: 'QA Copilot',
    description:
      'Turn requirements into reviewed test scenarios and risk-based coverage.',
    href: '/developer/qa-copilot',
    icon: Bot,
    status: 'In progress',
  },
  {
    title: 'Agentic Testing',
    description:
      'Validate a scenario, create an execution plan, and run controlled browser tests.',
    href: '/developer/agentic-testing',
    icon: FlaskConical,
    status: 'Foundation',
  },
  {
    title: 'QA Intelligence',
    description:
      'Triage findings, assess evidence quality, and prepare results for human review.',
    href: '/developer/qa-intelligence',
    icon: Bug,
    status: 'Planned',
  },
]

const foundations = [
  {
    title: 'Scenario validation',
    detail: 'Strict Pydantic contracts and explicit browser-origin allowlists.',
    icon: ShieldCheck,
    status: 'Implemented',
  },
  {
    title: 'Workflow planning',
    detail: 'A side-effect-free LangGraph validation and planning graph.',
    icon: GitBranch,
    status: 'Implemented',
  },
  {
    title: 'Deterministic run contract',
    detail: 'Validated step results and derived passed, failed, blocked, or inconclusive verdicts.',
    icon: CheckCircle2,
    status: 'Implemented',
  },
  {
    title: 'Browser execution and evidence ingestion',
    detail: 'Playwright adapter, artifact storage, and run orchestration.',
    icon: CircleDashed,
    status: 'Next',
  },
]

export function DeveloperOverview() {
  return (
    <Main className='flex flex-1 flex-col gap-6'>
      <PageHeader
        title='Developer Workspace'
        description='Engineering workspace for controlled QA automation, agent workflows, and test evidence.'
      />

      <div className='grid gap-4 md:grid-cols-3'>
        {capabilities.map(({ title, description, href, icon: Icon, status }) => (
          <Link key={title} to={href} className='group block min-w-0'>
            <Card className='h-full transition-colors group-hover:border-primary/40'>
              <CardHeader className='space-y-3'>
                <div className='flex items-center justify-between gap-3'>
                  <span className='flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary'>
                    <Icon className='size-5' />
                  </span>
                  <Badge variant='outline'>{status}</Badge>
                </div>
                <CardTitle className='flex items-center gap-2 text-base'>
                  {title}
                  <ArrowRight className='size-4 text-muted-foreground transition-transform group-hover:translate-x-1' />
                </CardTitle>
                <CardDescription className='leading-6'>
                  {description}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      <section className='space-y-3'>
        <div>
          <h2 className='text-lg font-semibold tracking-tight'>
            Platform foundation
          </h2>
          <p className='text-sm text-muted-foreground'>
            Current implementation status — not simulated runtime metrics.
          </p>
        </div>
        <div className='grid gap-3 md:grid-cols-2'>
          {foundations.map(({ title, detail, icon: Icon, status }) => (
            <Card key={title}>
              <CardContent className='flex items-start gap-3 p-4'>
                <span className='mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground'>
                  <Icon className='size-4' />
                </span>
                <div className='min-w-0 flex-1 space-y-1'>
                  <div className='flex flex-wrap items-center justify-between gap-2'>
                    <p className='text-sm font-medium'>{title}</p>
                    <Badge variant={status === 'Implemented' ? 'secondary' : 'outline'}>
                      {status}
                    </Badge>
                  </div>
                  <p className='text-sm leading-5 text-muted-foreground'>
                    {detail}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2 text-base'>
            <Activity className='size-4 text-primary' />
            Execution safety
          </CardTitle>
          <CardDescription>
            The current graph validates and plans only. It does not launch a browser,
            call an LLM, or write to pharmacy business data.
          </CardDescription>
        </CardHeader>
      </Card>
    </Main>
  )
}

function DeveloperSection({
  title,
  description,
  status,
  scope,
}: {
  title: string
  description: string
  status: string
  scope: string[]
}) {
  return (
    <Main className='flex flex-1 flex-col gap-6'>
      <PageHeader title={title} description={description} />
      <Card>
        <CardHeader className='space-y-2'>
          <Badge variant='outline' className='w-fit'>
            {status}
          </Badge>
          <CardTitle className='text-base'>Workspace foundation</CardTitle>
          <CardDescription>
            This area is being built incrementally. The interface does not
            represent capabilities as operational until their backend and
            validation are connected.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className='space-y-3'>
            {scope.map((item) => (
              <li key={item} className='flex items-start gap-2 text-sm'>
                <CircleDashed className='mt-0.5 size-4 shrink-0 text-muted-foreground' />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </Main>
  )
}

export function DeveloperCopilot() {
  return (
    <DeveloperSection
      title='QA Copilot'
      description='Requirement analysis, risk assessment, and test scenario design.'
      status='In progress'
      scope={[
        'Requirement and acceptance-criteria intake.',
        'Ambiguity and risk identification.',
        'Structured scenario proposals with human review.',
      ]}
    />
  )
}

export function DeveloperAgenticTesting() {
  return (
    <DeveloperSection
      title='Agentic Testing'
      description='Controlled planning and execution of browser test scenarios.'
      status='Planning foundation implemented'
      scope={[
        'Pydantic scenario validation and explicit origin allowlisting.',
        'LangGraph execution-plan generation with bounded declarative steps.',
        'Next: Playwright adapter, redirect-origin enforcement, and evidence capture.',
      ]}
    />
  )
}

export function DeveloperIntelligence() {
  return (
    <DeveloperSection
      title='QA Intelligence'
      description='Evidence-based failure analysis, triage, and quality evaluation.'
      status='Planned'
      scope={[
        'Failure grouping and reproducibility analysis.',
        'Advisory severity and confidence classification.',
        'Evidence completeness and evaluation harness.',
        'Human confirmation remains authoritative for defect and release decisions.',
      ]}
    />
  )
}
