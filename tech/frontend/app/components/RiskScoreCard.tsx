'use client';

interface RiskScoreCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: 'red' | 'orange' | 'green' | 'blue';
  // API placeholder
  data?: {
    title: string;
    value: string;
    subtitle: string;
  };
}

export default function RiskScoreCard({
  title,
  value,
  subtitle,
  color,
  data,
}: RiskScoreCardProps) {
  // Use API data if available, otherwise use props
  const displayTitle = data?.title || title;
  const displayValue = data?.value || value;
  const displaySubtitle = data?.subtitle || subtitle;

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
      <h3 className="text-sm font-medium text-gray-600 mb-2">
        {displayTitle}
      </h3>
      <p className={`text-3xl font-bold mb-1 ${colorClasses[color]}`}>
        {displayValue}
      </p>
      <p className={`text-sm ${subtitleColorClasses[color]}`}>
        {displaySubtitle}
      </p>
    </div>
  );
}
