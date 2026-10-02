import type { Directive } from 'vue'
import { useAuthStore } from '../stores/auth'

export const permission: Directive<HTMLElement, string> = {
  mounted(el, binding) {
    if (!useAuthStore().hasPermission(binding.value)) el.remove()
  },
}
