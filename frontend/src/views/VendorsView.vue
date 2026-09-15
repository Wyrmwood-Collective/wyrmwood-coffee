<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { client, authHeaders, extractErrorDetail } from "@/api/client";
import FormMessage from "@/components/FormMessage.vue";
import LinkButton from "@/components/LinkButton.vue";
import type { components } from "@/types/api";

type Vendor = components["schemas"]["VendorRead"];
type VendorContactRead = components["schemas"]["VendorContactRead"];
type VendorContactCreate = components["schemas"]["VendorContactCreateNested"];

const vendors = ref<Vendor[]>([]);
const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  const { data, error } = await client.GET("/vendors");
  if (error) {
    errorMessage.value = "Could not load vendors.";
  } else {
    vendors.value = data;
  }
  loading.value = false;
});

// represents a vendor contact being in-place edited
interface VendorDraft {
  name: string;
  active: boolean;
  contacts: VendorContactRead[];
}

const drafts = ref<Record<number, VendorDraft>>({});
const savingVendorIds = ref<Set<number>>(new Set());
const deletingVendorId = ref<number | null>(null);

// the actual rendered values (saved or draft)
const rows = computed(() =>
  vendors.value.map((vendor) => ({ vendor, draft: drafts.value[vendor.id] })),
);

function startEdit(vendor: Vendor) {
  drafts.value[vendor.id] = {
    name: vendor.name,
    active: vendor.active,
    contacts: vendor.contacts.map((contact) => ({ ...contact })),
  };
}

function cancelEdit(vendorId: number) {
  delete drafts.value[vendorId];
}

// use negative IDs for new vendor contacts
let nextNewContactId = -1;

function addContact(vendorId: number) {
  const draft = drafts.value[vendorId];
  if (!draft) {
    return;
  }
  draft.contacts.push({
    id: nextNewContactId--,
    name: "",
    role: "",
    phone: "",
    email: "",
    vendor_id: vendorId,
  });
}

function removeContact(vendorId: number, index: number) {
  drafts.value[vendorId]?.contacts.splice(index, 1);
}

// removes negative IDs before submission (API treats contacts with no ID as new)
function toContactPayload(contact: VendorContactRead) {
  const { id, vendor_id: _vendorId, ...rest } = contact;
  return id > 0 ? { id, ...rest } : { ...rest };
}

async function saveEdit(vendorId: number) {
  const draft = drafts.value[vendorId];
  if (!draft) {
    return;
  }

  savingVendorIds.value.add(vendorId);
  errorMessage.value = "";

  const { data, error } = await client.PUT("/vendors/{id}", {
    params: { path: { id: vendorId } },
    headers: authHeaders(),
    body: {
      name: draft.name,
      active: draft.active,
      contacts: draft.contacts.map(toContactPayload),
    },
  });

  savingVendorIds.value.delete(vendorId);

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not save vendor.");
    return;
  }

  const index = vendors.value.findIndex((vendor) => vendor.id === data.id);
  vendors.value[index] = data;
  cancelEdit(vendorId);
}

async function deleteVendor(vendor: Vendor) {
  errorMessage.value = "";
  deletingVendorId.value = vendor.id;

  const { error } = await client.DELETE("/vendors/{id}", {
    params: { path: { id: vendor.id } },
    headers: authHeaders(),
  });

  deletingVendorId.value = null;

  if (error) {
    errorMessage.value = extractErrorDetail(error, "Could not delete vendor.");
    return;
  }

  vendors.value = vendors.value.filter((v) => v.id !== vendor.id);
  cancelEdit(vendor.id);
}

// represents a vendor being in-place edited
interface NewVendorDraft {
  name: string;
  active: boolean;
  contacts: VendorContactCreate[];
}

function emptyVendorDraft(): NewVendorDraft {
  return { name: "", active: true, contacts: [] };
}

const creatingVendor = ref(false);
const savingNewVendor = ref(false);
const newVendorDraft = ref<NewVendorDraft>(emptyVendorDraft());

function startCreate() {
  newVendorDraft.value = emptyVendorDraft();
  creatingVendor.value = true;
}

function cancelCreate() {
  creatingVendor.value = false;
}

function addNewVendorContact() {
  newVendorDraft.value.contacts.push({ name: "", role: "", phone: "", email: "" });
}

function removeNewVendorContact(index: number) {
  newVendorDraft.value.contacts.splice(index, 1);
}

async function createVendor() {
  savingNewVendor.value = true;
  errorMessage.value = "";

  const { data, error } = await client.POST("/vendors", {
    headers: authHeaders(),
    body: newVendorDraft.value,
  });

  savingNewVendor.value = false;

  if (!data) {
    errorMessage.value = extractErrorDetail(error, "Could not create vendor.");
    return;
  }

  vendors.value.push(data);
  creatingVendor.value = false;
}
</script>

<style scoped>
/* Ledger layout, built from nested lists rather than a table — contacts
   stopped being real columns once they moved to their own lines, so the
   row/cell model was only doing alignment work, not describing tabular
   data. CSS Grid does the same alignment here without claiming to be a
   grid of data it isn't. Each vendor is one entry (bordered as a whole,
   like a ledger account) containing indented contact "memo" lines.
   Shared ledger styling (independent of column layout) lives in the main
   stylesheet; only this page's column widths stay here. */
.page {
  display: block;
  color: var(--ink);
}

/* Every column is a fixed length (em/px) rather than `auto` or a second
   `fr` track — each header/row is its own independent grid container, so
   a content-sized track (auto) would size differently per row (e.g. the
   empty header cell vs. "Edit Delete" vs. "Save Cancel") and throw off
   alignment between rows even with identical templates. */
.ledger-head,
.row-main {
  grid-template-columns: 3em 1fr 90px 170px;
}

.sub-item-line {
  grid-template-columns: 160px 140px 130px 1fr auto;
}
</style>

<template>
  <main class="page">
    <h1>Vendors</h1>
    <FormMessage :text="errorMessage" type="error" />
    <div v-if="loading">Loading...</div>
    <template v-else>
      <div class="ledger-toolbar">
        <LinkButton :disabled="creatingVendor" @click="startCreate">New vendor</LinkButton>
      </div>
      <div class="ledger-head">
        <span class="row-id">ID</span>
        <span>Name</span>
        <span>Active</span>
        <span></span>
      </div>
      <ul class="ledger">
        <li v-if="creatingVendor" class="ledger-row">
          <div class="row-main">
            <span class="row-id">new</span>
            <input
              v-model="newVendorDraft.name"
              type="text"
              class="field"
              placeholder="Vendor name"
            />
            <select v-model="newVendorDraft.active" class="field">
              <option :value="true">true</option>
              <option :value="false">false</option>
            </select>
            <span class="row-actions">
              <LinkButton :disabled="savingNewVendor" @click="createVendor">
                {{ savingNewVendor ? "Saving..." : "Save" }}
              </LinkButton>
              <LinkButton :disabled="savingNewVendor" @click="cancelCreate">Cancel</LinkButton>
            </span>
          </div>
          <ul class="sub-list">
            <li v-if="!newVendorDraft.contacts.length" class="no-sub-items">No contacts on file</li>
            <li v-for="(contact, i) in newVendorDraft.contacts" :key="i" class="sub-item-line">
              <input v-model="contact.name" type="text" class="field" placeholder="Contact name" />
              <input v-model="contact.role" type="text" class="field" placeholder="Role" />
              <input v-model="contact.phone" type="text" class="field" placeholder="Phone" />
              <input v-model="contact.email" type="text" class="field" placeholder="Email" />
              <LinkButton @click="removeNewVendorContact(i)">Remove</LinkButton>
            </li>
            <li class="sub-item-actions">
              <LinkButton @click="addNewVendorContact">Add contact</LinkButton>
            </li>
          </ul>
        </li>
        <li v-for="row in rows" :key="row.vendor.id" class="ledger-row">
          <div class="row-main">
            <span class="row-id">{{ row.vendor.id }}</span>
            <template v-if="row.draft">
              <input v-model="row.draft.name" type="text" class="field" placeholder="Vendor name" />
              <select v-model="row.draft.active" class="field">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
              <span class="row-actions">
                <LinkButton
                  :disabled="savingVendorIds.has(row.vendor.id)"
                  @click="saveEdit(row.vendor.id)"
                >
                  {{ savingVendorIds.has(row.vendor.id) ? "Saving..." : "Save" }}
                </LinkButton>
                <LinkButton
                  :disabled="savingVendorIds.has(row.vendor.id)"
                  @click="cancelEdit(row.vendor.id)"
                >
                  Cancel
                </LinkButton>
              </span>
            </template>
            <template v-else>
              <span>{{ row.vendor.name }}</span>
              <span>{{ row.vendor.active }}</span>
              <span class="row-actions">
                <LinkButton @click="startEdit(row.vendor)">Edit</LinkButton>
                <LinkButton
                  :disabled="deletingVendorId === row.vendor.id"
                  @click="deleteVendor(row.vendor)"
                >
                  {{ deletingVendorId === row.vendor.id ? "Deleting..." : "Delete" }}
                </LinkButton>
              </span>
            </template>
          </div>
          <ul v-if="row.draft" class="sub-list">
            <li v-if="!row.draft.contacts.length" class="no-sub-items">No contacts on file</li>
            <li v-for="(contact, i) in row.draft.contacts" :key="contact.id" class="sub-item-line">
              <input v-model="contact.name" type="text" class="field" placeholder="Contact name" />
              <input v-model="contact.role" type="text" class="field" placeholder="Role" />
              <input v-model="contact.phone" type="text" class="field" placeholder="Phone" />
              <input v-model="contact.email" type="text" class="field" placeholder="Email" />
              <LinkButton @click="removeContact(row.vendor.id, i)">Remove</LinkButton>
            </li>
            <li class="sub-item-actions">
              <LinkButton @click="addContact(row.vendor.id)">Add contact</LinkButton>
            </li>
          </ul>
          <ul v-else class="sub-list">
            <li v-if="!row.vendor.contacts.length" class="no-sub-items">No contacts on file</li>
            <li v-for="contact in row.vendor.contacts" :key="contact.id" class="sub-item-line">
              <span>{{ contact.name }}</span>
              <span>{{ contact.role }}</span>
              <span>{{ contact.phone }}</span>
              <span>{{ contact.email }}</span>
            </li>
          </ul>
        </li>
      </ul>
    </template>
  </main>
</template>
