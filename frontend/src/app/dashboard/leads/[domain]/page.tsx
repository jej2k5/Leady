import { LeadsListPlaceholder } from '@/components/leads/LeadsListPlaceholder';

type DomainLeadsPageProps = {
  params: Promise<{
    domain: string;
  }>;
};

export default async function DomainLeadsPage({ params }: DomainLeadsPageProps) {
  const { domain } = await params;

  return <LeadsListPlaceholder title={`Leads for ${domain}`} />;
}
