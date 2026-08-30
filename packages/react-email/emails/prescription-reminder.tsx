/**
 * Prescription Reminder Email Template.
 */
import { Body, Container, Head, Heading, Html, Preview, Text, Button } from '@react-email/components';

interface Props {
  patientName: string;
  medications: Array<{name: string; dosage: string; frequency: string}>;
  pharmacyName: string;
  confirmUrl: string;
}

export default function PrescriptionReminderEmail({
  patientName = '{{ patientName }}',
  medications = [],
  pharmacyName = '{{ pharmacyName }}',
  confirmUrl = '{{ confirmUrl }}',
}: Props) {
  return (
    <Html>
      <Head />
      <Preview>Medication Reminder</Preview>
      <Body style={{ backgroundColor: '#f5f5f5', fontFamily: 'Arial' }}>
        <Container style={{ maxWidth: 600, margin: '0 auto', background: 'white', padding: 20, borderRadius: 8 }}>
          <Heading style={{ color: '#1a73e8' }}>Pharmaviyum CRM</Heading>
          <Text>Hello, {patientName}!</Text>
          <Text>Here are your medications for today:</Text>
          {medications.map((med, i) => (
            <Text key={i}><strong>{med.name}</strong> - {med.dosage} ({med.frequency})</Text>
          ))}
          <Button href={confirmUrl} style={{
            backgroundColor: '#1a73e8', color: 'white',
            padding: '12px 24px', borderRadius: 6, textDecoration: 'none',
          }}>Confirm Intake</Button>
          <Text style={{ fontSize: 14, color: '#666' }}>Contact: {pharmacyName}</Text>
        </Container>
      </Body>
    </Html>
  );
}
