import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      <h1>Leady Frontend</h1>
      <p>Scaffold for auth and dashboard routes.</p>
      <Link href="/login">Go to login</Link>
    </main>
  );
}
