import { Link, createFileRoute } from '@tanstack/react-router'
import { ArrowLeft, BookOpen, Network, ShieldCheck } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const Route = createFileRoute(
  '/_authenticated/settings/developer/ansible'
)({
  component: AnsibleDocumentationPage,
})

type DocumentationSection = {
  id: string
  title: string
  paragraphs?: string[]
  bullets?: string[]
  code?: string
}

const sections: DocumentationSection[] = [
  {
    id: 'overview',
    title: 'What Ansible is',
    paragraphs: [
      'Ansible is an agentless IT automation and configuration-management tool. It connects to Linux hosts over SSH and applies declarative playbooks describing the desired system state. Pharmacy servers do not need a permanently installed Ansible agent.',
      'For Pharmaviyum, Ansible is the controlled operations layer used to prepare and maintain Pharmacy Edge servers. It standardizes host configuration, reduces manual configuration drift, deploys reviewed application releases, verifies readiness, and runs approved maintenance procedures.',
      'Ansible does not replace the application, PostgreSQL, local POS, or Central synchronization service. It automates the infrastructure on which those components run.',
    ],
  },
  {
    id: 'rollout',
    title: 'Initial rollout: 1–10 pharmacies',
    bullets: [
      'Start with one isolated lab pharmacy and validate the complete lifecycle.',
      'Expand to 2–3 pilot sites only after lab acceptance.',
      'Increase gradually, never exceeding ten active pharmacy hosts in this profile.',
      'Use serial deployment with one host per wave; any failed host or readiness check stops progression.',
      'Every pharmacy must have unique site identity, database credentials, Edge sync identity, backup namespace, and operational owner.',
    ],
  },
  {
    id: 'future-scale',
    title: 'Future scale: up to 100 pharmacies',
    paragraphs: [
      'The target architecture is designed to accommodate up to 100 independent Pharmacy Edge sites. This is a future capacity objective, not the current active rollout size and not evidence that a 100-site fleet has been load-tested or accepted.',
      'The Ansible configuration separates max_supported_pharmacy_sites: 100 from active_rollout_limit: 10. The starter deployment and migration playbooks must continue to reject inventories larger than ten until a separate capacity, security, resilience, and operational review authorizes expansion.',
    ],
    bullets: [
      'Use a CMDB-backed dynamic inventory; keep Central hosts separate from Pharmacy Edge hosts.',
      'Divide Edge sites into explicit canary and rollout-wave groups. Preserve unique pharmacy ID, site code, Edge identity, PostgreSQL credentials, and backup namespace for every site.',
      'Keep the initial rollout serial and fail-fast. Any future batch size must be justified by measured controller, network, registry, database, and site-health capacity.',
      'Before increasing the active limit, complete fleet load and failure tests, backup/restore drills, sync backlog and replay validation, monitoring and alerting, and documented RPO/RTO.',
      'Treat ansible/inventory/examples/fleet-100.yml as a non-runnable schema example, never as a production inventory.',
      'The 100-site profile is an architecture provision only. Do not change the active ten-site guardrail as part of the current rollout.',
    ],
  },
  {
    id: 'architecture',
    title: 'Pharmacy Edge operating model',
    paragraphs: [
      'A pharmacy has a dedicated Edge host on its local network. Local POS workflows must not require a continuous WAN connection to Central for every transaction. The Edge host retains local operational data and synchronizes with Central when connectivity is available.',
      'Run Ansible from a protected automation controller or approved CI runner. It connects to the selected Edge host over a restricted SSH management path. It is not a public web service and must not run from an employee POS workstation.',
    ],
    code: 'Protected Ansible Controller\n  | SSH over restricted management network\n  v\nPharmacy Edge Host (one site)\n  - Docker Engine and Compose\n  - Pharmaviyum API and local PostgreSQL\n  - Local sync services and backup artifacts\n  | HTTPS synchronization when WAN is available\n  v\nPharmaviyum Central',
  },
  {
    id: 'prerequisites',
    title: 'Pharmacy prerequisites',
    bullets: [
      'Supported Linux server or VM; assessed CPU, memory, storage, and power protection.',
      'Stable hostname and reserved management IP address.',
      'SSH restricted to the approved management network or controller.',
      'Dedicated non-root automation account with narrowly scoped privilege escalation.',
      'SSH host keys verified out of band; host-key checking must remain enabled.',
      'Docker Engine and Compose versions matching repository pins.',
      'Required outbound registry and Central endpoint access.',
      'Time synchronization, firewall, disk, and UPS monitoring.',
      'Unique pharmacy identity, site credentials, change reference, maintenance window, and recovery contact.',
    ],
  },
  {
    id: 'controller',
    title: 'Prepare the Ansible controller',
    bullets: [
      'Use an isolated controller such as AWX/AAP or an approved CI runner.',
      'Pin Ansible Core and collection versions.',
      'Store SSH keys and Vault credentials in the controller secret store.',
      'Restrict job launch permissions and require approval for production inventories.',
      'Keep inventories and playbooks in version control; never commit decrypted Vault files or secrets.',
      'Record operator, commit, image digest, target site, change reference, and job result.',
    ],
  },
  {
    id: 'inventory',
    title: 'Create a one-site inventory',
    paragraphs: [
      'The repository includes an isolated lab inventory at ansible/inventory/lab/hosts.yml. It reads the lab host, SSH user, and lab database password from protected runtime environment variables. Review it before use; never point it at a live pharmacy.',
      'Production inventory must define a real SSH endpoint and user, unique pharmacy_id and site_code, and a unique per-pharmacy postgres_password. Store site-specific values in encrypted host variables or an approved secret manager.',
    ],
  },
  {
    id: 'secrets',
    title: 'Release inputs and secrets',
    bullets: [
      'PHARMAVIYUM_APP_VERSION: immutable release tag; never use latest.',
      'PHARMAVIYUM_BACKEND_IMAGE_DIGEST: approved sha256 image digest.',
      'Unique per-host postgres_password, supplied through encrypted host variables or a secret manager.',
      'Unique pharmacy_id and site_code for every site.',
      'Explicit approved docker_package_versions pins for all required Docker packages; deployment fails closed if a pin is missing.',
      'Least-privilege registry username and token.',
      'Edge node UUID, Edge token, and Central HTTPS URL must be configured together or all remain disabled.',
    ],
    paragraphs: [
      'Use protected controller credentials and masked runtime variables. Never place secrets in shell history, command-line arguments, tickets, source control, or logs. Do not reuse credentials between pharmacies.',
    ],
  },
  {
    id: 'deployment',
    title: 'Deployment workflow',
    bullets: [
      'Review the target commit and playbook diff.',
      'Confirm only approved pharmacy hosts are selected and the fleet is within the ten-site cap.',
      'Pass YAML syntax, Ansible lint, role, and CI checks.',
      'Test in an isolated lab before any pharmacy pilot.',
      'Verify immutable image digest, unique credentials, and change approval.',
      'Deploy to the explicitly approved target only.',
      'Verify /ready, containers, database, disk, and sync health.',
      'Perform a POS smoke test and prove local sales continue during a WAN outage.',
      'Record release digest and test evidence before adding another site.',
    ],
    code: 'cd ansible\nansible-playbook -i inventory/lab/hosts.yml playbooks/deploy.yml --limit pharmacy-edge-lab-01',
    paragraphs: [
      'The controller must provide required lab connection/release variables and approved Docker package pins at runtime. The lab inventory must never point to a live pharmacy. The production inventory is the default in ansible.cfg, so pass the intended lab inventory explicitly.',
    ],
  },
  {
    id: 'migrations',
    title: 'Database migrations',
    paragraphs: [
      'Application deployment must not implicitly run Alembic migrations. A migration is a separate reviewed operation requiring its own playbook, compatibility checks, explicit approval and change reference, verified backup, controlled target selection, and post-migration readiness validation.',
    ],
  },
  {
    id: 'recovery',
    title: 'Backup and recovery',
    paragraphs: [
      'A backup stored only on the pharmacy Edge host is not disaster recovery. Production acceptance requires encrypted off-site storage independent of the pharmacy, site-scoped upload identities, checksum verification, centrally controlled retention, documented RPO/RTO, and restore from the remote copy into an isolated database.',
      'Validate critical tables, business row counts, migration version, and application readiness. Never test a restore by overwriting the live pharmacy database.',
    ],
  },
  {
    id: 'security',
    title: 'Security safeguards',
    bullets: [
      'SSH key authentication, host-key verification, least privilege, and protected controller credentials.',
      'Immutable image digests and unique per-pharmacy database and Edge credentials.',
      'Database ports must not be publicly reachable; expose only required services.',
      'Use check mode where supported, but always validate in a lab.',
      'Roles must be idempotent; a second run should produce no unexpected changes.',
      'Deployment, migration, backup, restore, and rollback remain separate auditable operations.',
    ],
  },
  {
    id: 'acceptance',
    title: 'Site acceptance checklist',
    bullets: [
      'Host hardening, SSH, firewall, time sync, and UPS monitoring.',
      'Reproducible Ansible run and clean second-run idempotency.',
      'Immutable release and successful readiness checks.',
      'Local POS transaction during WAN outage.',
      'Safe synchronization replay without duplicate sales or stock movements.',
      'Verified local and encrypted off-site backups.',
      'Successful isolated restore from off-site copy.',
      'Monitoring for disk, database, backup age, sync backlog, and last sync.',
      'Documented site owner, RPO/RTO, rollback owner, and support contact.',
    ],
  },
]

function AnsibleDocumentationPage() {
  return (
    <main className='space-y-6 p-4 md:p-6'>
      <div className='flex flex-wrap items-center justify-between gap-3'>
        <Link
          to='/settings/developer'
          className='inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground'
        >
          <ArrowLeft className='size-4' />
          Developer Settings
        </Link>
        <span className='inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium'>
          <Network className='size-3.5' />
          Ansible
        </span>
      </div>

      <header className='space-y-2'>
        <div className='flex items-center gap-2 text-sm text-muted-foreground'>
          <BookOpen className='size-4' />
          Developer documentation
        </div>
        <h1 className='text-3xl font-semibold tracking-tight'>
          Ansible — Pharmacy Edge Setup Guide
        </h1>
        <p className='max-w-3xl text-muted-foreground'>
          An operational guide for securely preparing, deploying, and
          maintaining Pharmaviyum Edge servers in pharmacies.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <ShieldCheck className='size-5' />
            Initial rollout policy
          </CardTitle>
          <CardDescription>Current Ansible rollout boundary</CardDescription>
        </CardHeader>
        <CardContent className='space-y-2'>
          <p className='text-2xl font-semibold tabular-nums'>1–10 pharmacies</p>
          <p className='text-sm text-muted-foreground'>
            Begin with one lab site, then a small pilot, and expand gradually.
            Deployment is serial (one pharmacy at a time) and stops on a failed
            readiness check. The limit is an operational guardrail, not proof
            that ten production sites have been accepted.
          </p>
        </CardContent>
      </Card>

      <div className='grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]'>
        <article className='min-w-0 space-y-8'>
          {sections.map((section, index) => (
            <section
              key={section.id}
              id={section.id}
              className='scroll-mt-6 space-y-3'
            >
              <h2 className='text-xl font-semibold'>
                {index + 1}. {section.title}
              </h2>
              {section.paragraphs?.map((paragraph) => (
                <p
                  key={paragraph}
                  className='text-sm leading-6 text-muted-foreground'
                >
                  {paragraph}
                </p>
              ))}
              {section.bullets && (
                <ul className='list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
                  {section.bullets.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
              {section.code && (
                <pre className='overflow-x-auto rounded-lg border bg-muted/40 p-4 text-xs leading-6'>
                  {section.code}
                </pre>
              )}
            </section>
          ))}
          <p className='border-t pt-4 text-sm leading-6 text-muted-foreground'>
            This guide describes the intended process and the initial ten-site
            boundary. It does not claim that the production acceptance checklist
            is complete. Lab evidence is still required for full Edge lifecycle,
            off-site recovery, offline POS, UPS monitoring, and end-to-end
            synchronization. Do not deploy to real pharmacy hosts until the
            relevant changes are approved and lab and pilot gates have passed.
          </p>
        </article>

        <aside className='h-fit rounded-lg border p-4 lg:sticky lg:top-6'>
          <h2 className='mb-3 text-sm font-semibold'>On this page</h2>
          <nav className='space-y-2'>
            {sections.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className='block text-sm text-muted-foreground hover:text-foreground'
              >
                {section.title}
              </a>
            ))}
          </nav>
        </aside>
      </div>
    </main>
  )
}
