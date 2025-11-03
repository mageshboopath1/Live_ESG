<template>
  <Radar :data="chartData" :options="chartOptions" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Radar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions
} from 'chart.js'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

interface Props {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
  }[]
  title?: string
  max?: number
  tooltipCallback?: (value: number, label: string, datasetLabel: string) => string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  max: 100
})

const chartData = computed<ChartData<'radar'>>(() => ({
  labels: props.labels,
  datasets: props.datasets.map(ds => ({
    label: ds.label,
    data: ds.data,
    borderColor: ds.borderColor || 'rgba(99, 102, 241, 1)',
    backgroundColor: ds.backgroundColor || 'rgba(99, 102, 241, 0.2)',
    borderWidth: 2,
    pointRadius: 3,
    pointHoverRadius: 5,
    pointBackgroundColor: ds.borderColor || 'rgba(99, 102, 241, 1)',
    pointBorderColor: '#fff',
    pointBorderWidth: 2
  }))
}))

const chartOptions = computed<ChartOptions<'radar'>>(() => ({
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
      callbacks: {
        label: (context) => {
          const value = context.parsed.r
          const label = context.dataset.label || ''
          const dataLabel = context.label
          
          if (props.tooltipCallback) {
            return props.tooltipCallback(value, dataLabel, label)
          }
          
          return `${label}: ${value !== null ? value.toFixed(2) : 'N/A'}`
        }
      }
    }
  },
  scales: {
    r: {
      beginAtZero: true,
      max: props.max,
      ticks: {
        stepSize: props.max / 5
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      },
      pointLabels: {
        font: {
          size: 12
        }
      }
    }
  }
}))
</script>
