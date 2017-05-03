def model_policy_veg(pk):
    # TODO: this should be made in to a real model_policy
    with transaction.atomic():
        veg = VEGTenant.objects.select_for_update().filter(pk=pk)
        if not veg:
            return
        veg = veg[0]
        veg.manage_container()
        veg.manage_vrouter()
        veg.cleanup_orphans()


