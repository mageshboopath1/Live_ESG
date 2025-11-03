<template>
  <Bar :data="chartData" :options="chartOptions" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface Props {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string | string[]
    borderWidth?: number
  }[]
  title?: string
  yAxisLabel?: string
  xAxisLabel?: string
  horizontal?: boolean
  stacked?: boolean
  tooltipCallback?: (value: number, label: string, datasetLabel: string) => string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  yAxisLabel: '',
  xAxisLabel: '',
  horizontal: false,
  stacked: false
})

const chartData = computed<ChartData<'bar'>>(() => ({
  labels: props.labels,
  datasets: props.datasets.map(ds => ({
    label: ds.label,
    data: ds.data,
    backgroundColor: ds.backgroundColor || 'rgba(99, 102, 241, 0.8)',
    borderColor: ds.borderColor || 'rgba(99, 102, 241, 1)',
    borderWidth: ds.borderWidth || 1
  }))
}))

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  indexAxis: props.horizontal ? 'y' : 'x',
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
      stacked: props.stacked,
      title: {
        display: !!props.xAxisLabel,
        text: props.xAxisLabel
      },
      grid: {
        display: false
      }
    },
    y: {
      stacked: props.stacked,
      beginAtZero: true,
      title: {
        display: !!props.yAxisLabel,
        text: props.yAxisLabel
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      }
    }
  }
}))
</script>
