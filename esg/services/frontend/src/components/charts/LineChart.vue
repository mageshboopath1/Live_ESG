<template>
  <Line :data="chartData" :options="chartOptions" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartData,
  type ChartOptions
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface Props {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
    fill?: boolean
    tension?: number
  }[]
  title?: string
  yAxisLabel?: string
  xAxisLabel?: string
  yMin?: number
  yMax?: number
  tooltipCallback?: (value: number, label: string, datasetLabel: string) => string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  yAxisLabel: '',
  xAxisLabel: ''
})

const chartData = computed<ChartData<'line'>>(() => ({
  labels: props.labels,
  datasets: props.datasets.map(ds => ({
    label: ds.label,
    data: ds.data,
    borderColor: ds.borderColor || 'rgba(99, 102, 241, 1)',
    backgroundColor: ds.backgroundColor || 'rgba(99, 102, 241, 0.1)',
    fill: ds.fill !== undefined ? ds.fill : false,
    tension: ds.tension !== undefined ? ds.tension : 0.4,
    pointRadius: 4,
    pointHoverRadius: 6,
    pointBackgroundColor: ds.borderColor || 'rgba(99, 102, 241, 1)',
    pointBorderColor: '#fff',
    pointBorderWidth: 2
  }))
}))

const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: props.datasets.length > 1,
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 15
      }
    },
    title: {
      display: !!props.title,
      text: props.title,
      font: {
        size: 16,
        weight: 'bold'
      }
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: (context) => {
          const value = context.parsed.y
          const label = context.dataset.label || ''
          const dataLabel = context.label
          
          if (props.tooltipCallback && value !== null) {
            return props.tooltipCallback(value, dataLabel, label)
          }
          
          return `${label}: ${value !== null ? value.toFixed(2) : 'N/A'}`
        }
      }
    }
  },
  scales: {
    x: {
      title: {
        display: !!props.xAxisLabel,
        text: props.xAxisLabel
      },
      grid: {
        display: false
      }
    },
    y: {
      beginAtZero: props.yMin === undefined,
      min: props.yMin,
      max: props.yMax,
      title: {
        display: !!props.yAxisLabel,
        text: props.yAxisLabel
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      }
    }
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  }
}))
</script>
