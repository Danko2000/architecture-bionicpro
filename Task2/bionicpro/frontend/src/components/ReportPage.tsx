import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

// Описываем структуру отчета, которую отдает наш Python-бэкенд
interface ReportData {
  client_name: string;
  prosthesis_model: string;
  total_usage_hours: number;
  avg_response_time_ms: number;
  status: string;
}

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadReport = async () => {
    // 1. Проверяем авторизацию
    if (!keycloak?.token) {
      setError('Вы не авторизованы. Пожалуйста, войдите в систему.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setReport(null);

      // 2. Делаем запрос к API
      // process.env.REACT_APP_API_URL должен быть http://localhost:8000
      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${keycloak.token}`, // Токен для проверки "свой-чужой"
          'Content-Type': 'application/json'
        }
      });

      // 3. Обрабатываем статус ответа
      if (response.status === 404) {
        throw new Error('Отчет за сегодняшний день еще не сформирован. Данные обновляются раз в сутки.');
      }

      if (!response.ok) {
        throw new Error(`Ошибка сервера: ${response.statusText}`);
      }

      const data: ReportData = await response.json();
      setReport(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  };

  if (!initialized) {
    return <div className="p-8 text-center">Загрузка системы авторизации...</div>;
  }

  // Если пользователь не вошел, показываем кнопку входа
  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <div className="p-8 bg-white rounded-lg shadow-md text-center">
          <h2 className="text-xl mb-4">Доступ ограничен</h2>
          <button
            onClick={() => keycloak.login()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Войти в личный кабинет
          </button>
        </div>
      </div>
    );
  }

  // Основной UI для авторизованного пользователя
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 py-10">
      <div className="w-full max-w-2xl p-8 bg-white rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Отчет по телеметрии</h1>
        <p className="text-gray-500 mb-8">
          Здесь вы можете получить сводные данные об использовании вашего протеза.
        </p>
        
        <div className="flex justify-center mb-8">
          <button
            onClick={downloadReport}
            disabled={loading}
            className={`px-6 py-3 rounded-lg text-white font-medium text-lg transition-all ${
              loading 
                ? 'bg-blue-300 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
            }`}
          >
            {loading ? 'Генерация отчета...' : 'Получить мой отчёт'}
          </button>
        </div>

        {error && (
          <div className="p-4 mb-6 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p className="font-bold">Ошибка:</p>
            <p>{error}</p>
          </div>
        )}

        {report && (
          <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 animate-fade-in">
            <h3 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
              Результаты для: <span className="text-blue-600">{report.client_name}</span>
            </h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-500">Модель устройства</p>
                <p className="text-lg font-medium">{report.prosthesis_model}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Время использования</p>
                <p className="text-lg font-medium">{report.total_usage_hours.toFixed(1)} ч.</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Средняя задержка (Ping)</p>
                <p className="text-lg font-medium">{report.avg_response_time_ms.toFixed(0)} мс</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Статус состояния</p>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                  report.status === 'Отлично' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {report.status}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;
