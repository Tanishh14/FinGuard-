'use client';

interface RiskScoreCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: 'red' | 'orange' | 'green' | 'blue';
}

export default function RiskScoreCard({
  title,
  value,
  subtitle,
  color,
}: RiskScoreCardProps) {
  const colorClasses = {
    red: 'border-l-red-500 text-red-600',
    orange: 'border-l-orange-500 text-orange-600',
    green: 'border-l-green-500 text-green-600',
    blue: 'border-l-blue-500 text-blue-600',
  };

  const subtitleColorClasses = {
    red: 'text-red-500',
    orange: 'text-orange-500',
    green: 'text-green-500',
    blue: 'text-blue-400',
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm p-6 border-l-4 ${colorClasses[color]}`}
    >
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
      <p className={`text-3xl font-bold mb-1 ${colorClasses[color]}`}>{value}</p>
      <p className={`text-sm ${subtitleColorClasses[color]}`}>{subtitle}</p>
    </div>
  );
}
