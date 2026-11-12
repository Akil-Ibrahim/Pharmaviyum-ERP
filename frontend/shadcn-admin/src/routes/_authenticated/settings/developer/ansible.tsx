import { Link, createFileRoute } from '@tanstack/react-router'
import { ArrowLeft, BookOpen, CheckCircle2, Network, ShieldCheck } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const Route = createFileRoute('/_authenticated/settings/developer/ansible')({
  component: AnsibleDocumentationPage,
})

const sections = [
  { id: 'overview', title: 'What Ansible is' },
  { id: 'rollout', title: 'Initial rollout: 1–10 pharmacies' },
  { id: 'architecture', title: 'Pharmacy Edge operating model' },
  { id: 'prerequisites', title: 'Pharmacy prerequisites' },
  { id: 'controller', title: 'Prepare the Ansible controller' },
  { id: 'inventory', title: 'Create a one-site inventory' },
  { id: 'secrets', title: 'Release inputs and secrets' },
  { id: 'deployment', title: 'Deployment workflow' },
  { id: 'migrations', title: 'Database migrations' },
  { id: 'recovery', title: 'Backup and recovery' },
  { id: 'security', title: 'Security safeguards' },
  { id: 'acceptance', title: 'Site acceptance checklist' },
]

function AnsibleDocumentationPage() {
  return (
    <main className='space-y-6 p-4 md:p-6'>
      <div className='flex flex-wrap items-center justify-between gap-3'>
        <Link to='/settings/developer' className='inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground'>
          <ArrowLeft className='size-4' />Developer Settings
        </Link>
        <span className='inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium'>
          <Network className='size-3.5' />Ansible
        </span>
      </div>
      <header className='space-y-2'>
        <div className='flex items-center gap-2 text-sm text-muted-foreground'><BookOpen className='size-4' />Developer documentation</div>
        <h1 className='text-3xl font-semibold tracking-tight'>Ansible — Pharmacy Edge Setup Guide</h1>
        <p className='max-w-3xl text-muted-foreground'>An operational guide for securely preparing, deploying, and maintaining Pharmaviyum Edge servers in pharmacies.</p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'><ShieldCheck className='size-5' />Initial rollout policy</CardTitle>
          <CardDescription>Current Ansible rollout boundary</CardDescription>
        </CardHeader>
        <CardContent className='space-y-2'>
          <p className='text-2xl font-semibold tabular-nums'>1–10 pharmacies</p>
          <p className='text-sm text-muted-foreground'>Begin with one lab site, then a small pilot, and expand gradually. Deployment is serial (one pharmacy at a time) and stops on a failed readiness check. The limit is an operational guardrail, not proof that ten production sites have been accepted.</p>
        </CardContent>
      </Card>
      <div className='grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]'>
        <article className='min-w-0 space-y-8'>
          <section id='overview' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>1. What Ansible is</h2>
            <p className='text-sm leading-6 text-muted-foreground'>Ansible is an agentless IT automation and configuration-management tool. It connects to Linux hosts over SSH and applies declarative playbooks describing the desired system state. Pharmacy servers do not need a permanently installed Ansible agent.</p>
            <p className='text-sm leading-6 text-muted-foreground'>For Pharmaviyum, Ansible is the controlled operations layer used to prepare and maintain Pharmacy Edge servers. It standardizes host configuration, reduces manual configuration drift, deploys reviewed application releases, verifies readiness, and runs approved maintenance procedures consistently.</p>
            <p className='text-sm leading-6 text-muted-foreground'>Ansible does not replace the application, PostgreSQL, local POS, or Central synchronization service. It automates the infrastructure on which those components run.</p>
          </section>
          <section id='rollout' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>2. Initial rollout: 1–10 pharmacies</h2>
            <ul className='list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
              <li>Start with one isolated lab pharmacy and validate the complete lifecycle.</li>
              <li>Expand to 2–3 pilot sites only after lab acceptance.</li>
              <li>Increase gradually, never exceeding ten active pharmacy hosts in this profile.</li>
              <li>Use serial deployment with one host per wave; any failed host or readiness check stops progression.</li>
              <li>Every pharmacy must have unique site identity, database credentials, Edge sync identity, backup namespace, and operational owner.</li>
            </ul>
          </section>
          <section id='architecture' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>3. Pharmacy Edge operating model</h2>
            <p className='text-sm leading-6 text-muted-foreground'>A pharmacy has a dedicated Edge host on its local network. Local POS workflows must not require a continuous WAN connection to Central for every transaction. The Edge host retains local operational data and synchronizes with Central when connectivity is available.</p>
            <pre className='overflow-x-auto rounded-lg border bg-muted/40 p-4 text-xs leading-6'>Protected Ansible Controller{'
'}          | SSH over restricted management network{'
'}          v{'
'}Pharmacy Edge Host (one site){'
'}  - Docker Engine and Compose{'
'}  - Pharmaviyum API and local PostgreSQL{'
'}  - Local sync services and backup artifacts{'
'}          | HTTPS synchronization when WAN is available{'
'}          v{'
'}Pharmaviyum Central</pre>
            <p className='text-sm leading-6 text-muted-foreground'>Run Ansible from a protected automation controller or approved CI runner. Do not expose it as a public web service or run it from an employee POS workstation.</p>
          </section>
          <section id='prerequisites' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>4. Pharmacy prerequisites</h2>
            <ul className='list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
              <li>Supported Linux server or VM; assessed CPU, memory, storage, and power protection.</li>
              <li>Stable hostname and reserved management IP address.</li>
              <li>SSH restricted to the approved management network or controller.</li>
              <li>Dedicated non-root automation account with narrowly scoped privilege escalation.</li>
              <li>SSH host keys verified out of band; host-key checking must remain enabled.</li>
              <li>Docker Engine and Compose versions matching repository pins.</li>
              <li>Required outbound registry and Central endpoint access.</li>
              <li>Time synchronization, firewall, disk, and UPS monitoring.</li>
              <li>Unique pharmacy identity, site credentials, change reference, maintenance window, and recovery contact.</li>
            </ul>
          </section>
          <section id='controller' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>5. Prepare the Ansible controller</h2>
            <ul className='list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
              <li>Use an isolated controller such as AWX/AAP or an approved CI runner.</li>
              <li>Pin Ansible Core and collection versions.</li>
              <li>Store SSH keys and Vault credentials in the controller secret store.</li>
              <li>Restrict job launch permissions and require approval for production inventories.</li>
              <li>Keep inventories and playbooks in version control; never commit decrypted Vault files or secrets.</li>
              <li>Record operator, commit, image digest, target site, change reference, and job result.</li>
            </ul>
          </section>
          <section id='inventory' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>6. Create a one-site inventory</h2>
            <p className='text-sm leading-6 text-muted-foreground'>Begin with one lab host. Supply actual host connection details through a protected inventory source. The following is illustrative only:</p>
            <pre className='overflow-x-auto rounded-lg border bg-muted/40 p-4 text-xs leading-6'>[pharmacy_servers]{'\n'}pharmacy-lab-01 ansible_host=192.0.2.10 ansible_user=ansible{'\n\n'}[pharmacy_servers:vars]{'\n'}ansible_become=true</pre>
            <p className='text-sm leading-6 text-muted-foreground'>Replace the documentation-only IP address with an address from the pharmacy management network. Store site-specific values in encrypted host variables or an approved secret manager.</p>
          </section>
          <section id='secrets' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>7. Release inputs and secrets</h2>
            <ul className='list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
              <li><code>PHARMAVIYUM_APP_VERSION</code>: immutable release tag; never <code>latest</code>.</li>
              <li><code>PHARMAVIYUM_BACKEND_IMAGE_DIGEST</code>: approved <code>sha256</code> image digest.</li>
              <li>Unique <code>PHARMAVIYUM_POSTGRES_PASSWORD</code> per pharmacy.</li>
              <li>Least-privilege registry username and token.</li>
              <li>Edge node UUID, Edge token, and Central HTTPS URL must be configured together or all remain disabled.</li>
            </ul>
            <p className='text-sm leading-6 text-muted-foreground'>Use protected controller credentials and masked runtime variables. Never place secrets in shell history, command-line arguments, tickets, source control, or logs. Do not reuse credentials between pharmacies.</p>
          </section>
          <section id='deployment' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>8. Deployment workflow</h2>
            <ol className='list-decimal space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
              <li>Review the target commit and playbook diff.</li>
              <li>Confirm only approved pharmacy hosts are selected and the fleet is within the ten-site cap.</li>
              <li>Pass YAML syntax, Ansible lint, role, and CI checks.</li>
              <li>Test in an isolated lab before any pharmacy pilot.</li>
              <li>Verify immutable image digest, unique credentials, and change approval.</li>
              <li>Deploy to the explicitly approved target only.</li>
              <li>Verify <code>/ready</code>, containers, database, disk, and sync health.</li>
              <li>Perform a POS smoke test and prove local sales continue during a WAN outage.</li>
              <li>Record release digest and test evidence before adding another site.</li>
            </ol>
            <pre className='overflow-x-auto rounded-lg border bg-muted/40 p-4 text-xs leading-6'>ansible-playbook -i inventories/lab/hosts.yml ansible/playbooks/deploy.yml --limit pharmacy-lab-01</pre>
            <p className='text-sm leading-6 text-muted-foreground'>Confirm actual inventory and playbook paths in the checked-out repository revision before execution. Never run a production deployment from an unreviewed branch.</p>
          </section>
          <section id='migrations' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>9. Database migrations</h2>
            <p className='text-sm leading-6 text-muted-foreground'>Application deployment must not implicitly run Alembic migrations. A migration is a separate reviewed operation requiring its own playbook, compatibility checks, explicit approval and change reference, verified backup, controlled target selection, and post-migration readiness validation.</p>
          </section>
          <section id='recovery' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>10. Backup and recovery</h2>
            <p className='text-sm leading-6 text-muted-foreground'>A backup stored only on the pharmacy Edge host is not disaster recovery. Production acceptance requires encrypted off-site storage independent of the pharmacy, site-scoped upload identities, checksum verification, centrally controlled retention, documented RPO/RTO, and restore from the remote copy into an isolated database.</p>
            <p className='text-sm leading-6 text-muted-foreground'>Validate critical tables, business row counts, migration version, and application readiness. Never test a restore by overwriting the live pharmacy database.</p>
          </section>
          <section id='security' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>11. Security safeguards</h2>
            <ul className='list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground'>
              <li>SSH key authentication, host-key verification, least privilege, and protected controller credentials.</li>
              <li>Immutable image digests and unique per-pharmacy database and Edge credentials.</li>
              <li>Database ports must not be publicly reachable; expose only required services.</li>
              <li>Use check mode where supported, but always validate in a lab.</li>
              <li>Roles must be idempotent; a second run should produce no unexpected changes.</li>
              <li>Deployment, migration, backup, restore, and rollback remain separate auditable operations.</li>
            </ul>
          </section>
          <section id='acceptance' className='scroll-mt-6 space-y-3'>
            <h2 className='text-xl font-semibold'>12. Site acceptance checklist</h2>
            <ul className='space-y-2 text-sm leading-6 text-muted-foreground'>
              {['Host hardening, SSH, firewall, time sync, and UPS monitoring','Reproducible Ansible run and clean second-run idempotency','Immutable release and successful readiness checks','Local POS transaction during WAN outage','Safe synchronization replay without duplicate sales or stock movements','Verified local and encrypted off-site backups','Successful isolated restore from off-site copy','Monitoring for disk, database, backup age, sync backlog, and last sync','Documented site owner, RPO/RTO, rollback owner, and support contact'].map((item) => (
                <li key={item} className='flex items-start gap-2'><CheckCircle2 className='mt-0.5 size-4 shrink-0' />{item}</li>
              ))}
            </ul>
          </section>
          <p className='border-t pt-4 text-sm leading-6 text-muted-foreground'>This guide describes the intended process and the initial ten-site boundary. It does not claim that the production acceptance checklist is complete. Lab evidence is still required for full Edge lifecycle, off-site recovery, offline POS, UPS monitoring, and end-to-end synchronization. Do not deploy to real pharmacy hosts until the relevant changes are approved and lab and pilot gates have passed.</p>
        </article>
        <aside className='h-fit rounded-lg border p-4 lg:sticky lg:top-6'>
          <h2 className='mb-3 text-sm font-semibold'>On this page</h2>
          <nav className='space-y-2'>
            {sections.map((section) => (
              <a key={section.id} href={`#${section.id}`} className='block text-sm text-muted-foreground hover:text-foreground'>{section.title}</a>
            ))}
          </nav>
        </aside>
      </div>
    </main>
  )
}
